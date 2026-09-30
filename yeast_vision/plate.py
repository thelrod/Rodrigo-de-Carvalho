"""
Módulo de Detecção da Placa de Petri e Região de Interesse (ROI)
==============================================================
Detecta a circunferência da placa de Petri por Hough Circles e ajuste
de contornos, aplicando exclusão periférica adaptativa para eliminar
o menisco e reflexos da borda plástica sem usar corte arbitrário fixo.
"""

from typing import Tuple, Optional
import cv2
import numpy as np

from yeast_vision.contracts import PlateROIResult


def calculate_adaptive_meniscus_margin(
    image_bgr: np.ndarray,
    cx: float,
    cy: float,
    radius: float,
    plate_diameter_mm: float = 90.0,
    nominal_meniscus_mm: float = 3.5,
) -> float:
    """
    Calcula a margem de exclusão periférica adaptativa baseada na geometria
    física da placa de Petri (OpenCFU / ISO) e no perfil de borda.

    Em placas padrão de 90 mm (raio 45 mm), o menisco físico e a borda plástica
    ocupam aproximadamente 3.0 a 4.0 mm, correspondendo a ~7.5% - 8.5% do raio.
    """
    if radius <= 10.0:
        return 8.0

    nominal_pct = (nominal_meniscus_mm / (plate_diameter_mm / 2.0)) * 100.0  # ~7.8%

    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        r_test_min = int(radius * 0.82)
        r_test_max = int(radius * 0.98)

        angles = np.linspace(0, 2 * np.pi, 16, endpoint=False)
        profile_drops = []
        for a in angles:
            xs = [int(cx + r * np.cos(a)) for r in range(r_test_min, r_test_max, 2)]
            ys = [int(cy + r * np.sin(a)) for r in range(r_test_min, r_test_max, 2)]
            valid = [(x, y) for x, y in zip(xs, ys) if 0 <= x < w and 0 <= y < h]
            if len(valid) >= 5:
                vals = [float(gray[y, x]) for x, y in valid]
                grad = np.abs(np.diff(vals))
                if len(grad) > 0 and np.max(grad) > 25:
                    max_idx = np.argmax(grad)
                    frac = 1.0 - ((r_test_min + max_idx * 2) / radius)
                    profile_drops.append(frac * 100.0)

        if profile_drops:
            adaptive_margin = float(np.median(profile_drops)) + 0.8
            return float(round(np.clip(adaptive_margin, 5.0, 12.0), 2))
    except Exception:
        pass

    return round(nominal_pct, 2)


def detect_petri_dish(
    image_bgr: np.ndarray,
    exclusion_margin_pct: Optional[float] = 8.0,
    auto_margin: bool = False,
    expected_diameter_ratio_min: float = 0.40,
    expected_diameter_ratio_max: float = 0.98,
) -> Tuple[PlateROIResult, np.ndarray]:
    """
    Localiza a placa de Petri e gera a máscara binária de área analisável.

    Parameters
    ----------
    image_bgr : np.ndarray
        Imagem em formato BGR.
    exclusion_margin_pct : float, optional
        Percentual do raio a excluir da borda periférica (menisco).
    auto_margin : bool, optional
        Se True, calcula a margem adaptativamente via OpenCFU / perfil de menisco.
    expected_diameter_ratio_min : float
        Fração mínima da largura esperada para o diâmetro da placa.
    expected_diameter_ratio_max : float
        Fração máxima da largura esperada para o diâmetro da placa.

    Returns
    -------
    roi_result : PlateROIResult
        Contrato estruturado com coordenadas, raio e áreas.
    analyzable_mask : np.ndarray
        Máscara booleana/uint8 (255 na área útil, 0 fora).
    """
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("Imagem inválida fornecida para detecção de placa.")

    h, w = image_bgr.shape[:2]
    min_dim = min(h, w)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Tentativa Primária: Detecção por Contorno da Placa contra Fundo Escuro
    # Aplica blur leve e limiarização de Otsu
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Operação morfológica de fechamento para preencher lacunas no ágar
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_circle: Optional[Tuple[float, float, float]] = None

    if contours:
        # Pega o maior contorno por área
        largest_cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_cnt)
        total_img_area = float(h * w)

        # Se o maior contorno cobrir entre 15% e 90% da imagem
        if 0.15 * total_img_area <= area <= 0.95 * total_img_area:
            (cx, cy), radius = cv2.minEnclosingCircle(largest_cnt)
            diameter = 2.0 * radius
            if (expected_diameter_ratio_min * min_dim <= diameter <= expected_diameter_ratio_max * min_dim):
                best_circle = (float(cx), float(cy), float(radius))

    # 2. Fallback: Hough Circles se o contorno não for conclusivo
    if best_circle is None:
        min_radius = int(min_dim * (expected_diameter_ratio_min / 2.0))
        max_radius = int(min_dim * (expected_diameter_ratio_max / 2.0))

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dim / 2.0,
            param1=50,
            param2=30,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        if circles is not None and len(circles) > 0:
            c = circles[0][0]
            best_circle = (float(c[0]), float(c[1]), float(c[2]))

    # 3. Fallback de Segurança: Círculo central padrão se a imagem estiver sem borda visível
    if best_circle is None:
        cx, cy = w / 2.0, h / 2.0
        radius = (min_dim / 2.0) * 0.85
        best_circle = (cx, cy, radius)

    cx, cy, r_outer = best_circle

    # 4. Cálculo da Margem Adaptativa e Áreas
    if auto_margin or exclusion_margin_pct is None:
        resolved_margin_pct = calculate_adaptive_meniscus_margin(image_bgr, cx, cy, r_outer)
    else:
        resolved_margin_pct = float(exclusion_margin_pct)

    margin_factor = 1.0 - (resolved_margin_pct / 100.0)
    r_inner = r_outer * margin_factor

    # Gera máscara da área útil (r_inner)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (int(round(cx)), int(round(cy))), int(round(r_inner)), 255, -1)

    analyzable_area_px = int(np.count_nonzero(mask))
    total_plate_area_px = int(np.pi * (r_outer ** 2))
    excluded_peripheral_area_px = max(0, total_plate_area_px - analyzable_area_px)

    roi_result = PlateROIResult(
        center_x_px=round(cx, 2),
        center_y_px=round(cy, 2),
        radius_px=round(r_outer, 2),
        exclusion_margin_pct=round(resolved_margin_pct, 2),
        analyzable_area_px=analyzable_area_px,
        excluded_peripheral_area_px=excluded_peripheral_area_px,
    )

    return roi_result, mask
