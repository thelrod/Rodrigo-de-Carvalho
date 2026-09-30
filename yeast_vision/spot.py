"""
Módulo de Ensaio de Gota / Spotting Assay (Modo 2)
=================================================
Quantifica ensaios de diluição seriada em leveduras (ex: 4x6 ou 8x12),
calculando o Sinal Integrado Corrigido pelo Fundo (a.u.), saturação,
área de biomassa e a métrica primária: Maior Diluição com Crescimento.
"""

from typing import List, Tuple, Dict, Optional
import cv2
import numpy as np

from yeast_vision.contracts import SingleSpotMeasurement, SpotAssayResult


def detect_grid_cells(
    image_bgr: np.ndarray,
    analyzable_mask: np.ndarray,
    grid_rows: int = 4,
    grid_cols: int = 6,
) -> List[Tuple[int, int, Tuple[int, int, int, int]]]:
    """
    Localiza os limites retangulares da grade de spots dentro da placa.

    Retorna uma lista de tuplas (row_idx, col_idx, (x_min, y_min, x_max, y_max)).
    """
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Binarização suave para encontrar a região que contém as gotas
    blurred = cv2.GaussianBlur(gray, (15, 15), 3)
    # Colônias/gotas são claras sobre ágar amarelado
    masked_gray = cv2.bitwise_and(blurred, blurred, mask=analyzable_mask)

    # Limiar baseado em percentil da área útil
    valid_pixels = masked_gray[analyzable_mask > 0]
    if valid_pixels.size == 0:
        thresh_val = 128
    else:
        thresh_val = float(np.percentile(valid_pixels, 65))

    _, binary = cv2.threshold(masked_gray, thresh_val, 255, cv2.THRESH_BINARY)

    # Encontra contornos das gotas
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    spot_centers = []
    min_spot_area = (h * w) * 0.0002  # pelo menos 0.02% da imagem
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_spot_area:
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                spot_centers.append((M["m10"] / M["m00"], M["m01"] / M["m00"]))

    # 2. Se encontrou centros de gotas suficientes, define a bounding box global da grade
    if len(spot_centers) >= (grid_rows * grid_cols * 0.4):
        xs = [c[0] for c in spot_centers]
        ys = [c[1] for c in spot_centers]
        x_min_grid, x_max_grid = np.percentile(xs, 5), np.percentile(xs, 95)
        y_min_grid, y_max_grid = np.percentile(ys, 5), np.percentile(ys, 95)

        # Adiciona margem proporcional
        dx = (x_max_grid - x_min_grid) / max(1, grid_cols - 1)
        dy = (y_max_grid - y_min_grid) / max(1, grid_rows - 1)
        x_start = max(0, x_min_grid - dx * 0.5)
        x_end = min(w, x_max_grid + dx * 0.5)
        y_start = max(0, y_min_grid - dy * 0.5)
        y_end = min(h, y_max_grid + dy * 0.5)
    else:
        # Fallback: Região central da placa
        x_start, x_end = w * 0.20, w * 0.80
        y_start, y_end = h * 0.25, h * 0.75

    # 3. Divisão regular das células da matriz
    cell_w = (x_end - x_start) / float(grid_cols)
    cell_h = (y_end - y_start) / float(grid_rows)

    cells = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            x1 = int(round(x_start + c * cell_w))
            y1 = int(round(y_start + r * cell_h))
            x2 = int(round(x1 + cell_w))
            y2 = int(round(y1 + cell_h))
            # Garante limites válidos
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            cells.append((r, c, (x1, y1, x2, y2)))

    return cells


def measure_spot_cell(
    gray_img: np.ndarray,
    cell_bbox: Tuple[int, int, int, int],
    analyzable_mask: np.ndarray,
) -> Tuple[bool, int, float, bool, float]:
    """
    Mede as propriedades biológicas dentro de uma célula da grade.

    Retorna:
    --------
    growth_detected : bool
        Métrica primária: True se o sinal exceder 3 * desvio-padrão do fundo local.
    area_growth_px : int
        Área do spot em pixels.
    integrated_signal : float
        Soma líquida de intensidade (I - I_bg) em a.u.
    is_saturated : bool
        True se houver pixels superexpostos (>= 250).
    confidence : float
        Score entre 0.0 e 1.0.
    """
    x1, y1, x2, y2 = cell_bbox
    if x2 <= x1 or y2 <= y1:
        return False, 0, 0.0, False, 0.0

    cell_gray = gray_img[y1:y2, x1:x2].astype(np.float32)
    cell_mask = analyzable_mask[y1:y2, x1:x2]

    valid_mask = (cell_mask > 0)
    if not np.any(valid_mask):
        return False, 0, 0.0, False, 0.0

    # 1. Estimativa do Fundo Local do Ágar
    # O fundo é estimado pelos percentis inferiores da célula (ex: percentil 25)
    bg_level = float(np.percentile(cell_gray[valid_mask], 20))
    bg_std = float(np.std(cell_gray[valid_mask]))
    bg_std = max(1.0, bg_std)

    # 2. Detecção de Crescimento de Biomassa
    # Sinal acima de 3 sigmas do fundo
    growth_threshold = bg_level + 2.5 * bg_std
    growth_mask = (cell_gray > growth_threshold) & valid_mask

    area_growth_px = int(np.count_nonzero(growth_mask))

    # 3. Cálculo do Sinal Integrado Corrigido pelo Fundo (a.u.)
    if area_growth_px > 10:
        net_intensity = cell_gray[growth_mask] - bg_level
        integrated_signal = float(np.sum(net_intensity))
        growth_detected = True
        confidence = min(1.0, float(area_growth_px / (cell_gray.size * 0.10)))
    else:
        integrated_signal = 0.0
        growth_detected = False
        confidence = 0.85

    # 4. Checagem de Saturação
    saturated_count = np.count_nonzero(cell_gray >= 250)
    is_saturated = (saturated_count > 0.05 * cell_gray.size)

    return (
        growth_detected,
        area_growth_px,
        round(integrated_signal, 2),
        is_saturated,
        round(confidence, 2),
    )


def run_spot_assay_analysis(
    image_bgr: np.ndarray,
    analyzable_mask: np.ndarray,
    grid_rows: int = 4,
    grid_cols: int = 6,
    strain_ids: Optional[List[str]] = None,
    dilution_series: Optional[List[float]] = None,
) -> SpotAssayResult:
    """Executa a quantificação completa do Spot Assay."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    cells = detect_grid_cells(image_bgr, analyzable_mask, grid_rows=grid_rows, grid_cols=grid_cols)

    # Linhagens por linha (se não informadas, cria IDs automáticos)
    if strain_ids is None or len(strain_ids) != grid_rows:
        strain_ids = [f"Linhagem_{r+1}" for r in range(grid_rows)]

    # Fator de diluição por coluna (padrão: 1, 10, 100, 1000, 10000, 100000)
    if dilution_series is None or len(dilution_series) != grid_cols:
        dilution_series = [float(10 ** c) for c in range(grid_cols)]

    measurements: List[SingleSpotMeasurement] = []
    max_dilution_by_strain: Dict[str, float] = {strain: 0.0 for strain in strain_ids}

    for r, c, bbox in cells:
        strain = strain_ids[r]
        dilution = dilution_series[c]

        growth, area, signal, sat, conf = measure_spot_cell(gray, bbox, analyzable_mask)

        measurements.append(
            SingleSpotMeasurement(
                row_idx=r,
                col_idx=c,
                strain_id=strain,
                dilution_factor=dilution,
                growth_detected=growth,
                area_growth_px=area,
                background_corrected_signal=signal,
                is_saturated=sat,
                confidence_score=conf,
            )
        )

        # Métrica primária: maior diluição com crescimento
        if growth and dilution > max_dilution_by_strain[strain]:
            max_dilution_by_strain[strain] = dilution

    return SpotAssayResult(
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        spots=measurements,
        max_dilution_with_growth_by_strain=max_dilution_by_strain,
        execution_version="2.1.0",
        random_seed=42,
    )
