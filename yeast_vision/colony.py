"""
Módulo de Contagem de Colônias de Leveduras (Modo 1: Spread Plate)
================================================================
Implementa o pipeline determinístico em float32 para detecção,
separação de colônias confluentes por Watershed com marcadores,
extração morfométrica (área, circularidade, solidez) e cálculo de UFC/mL.
"""

from typing import List, Tuple, Optional
import cv2
import numpy as np
from scipy import ndimage as ndi

from yeast_vision.contracts import SingleColony, ColonyCountResult


def preprocess_plate_image(
    image_bgr: np.ndarray,
    analyzable_mask: np.ndarray,
    tophat_radius_px: int = 35,
) -> np.ndarray:
    """
    Pré-processa a imagem da placa em float32 para realçar colônias.

    Combina o canal de luminosidade (L do espaço Lab) com o inverso
    da saturação (S do espaço HSV) para desacoplar a colônia branca
    do fundo âmbar do ágar (YPD/YPGal/YPGLy).
    """
    # 1. Conversão para float32 no intervalo [0.0, 1.0] (ADR-0004)
    img_f32 = image_bgr.astype(np.float32) / 255.0

    # 2. Espaço de Cor Lab e HSV
    lab = cv2.cvtColor((img_f32 * 255.0).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32) / 255.0
    hsv = cv2.cvtColor((img_f32 * 255.0).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32) / 255.0

    l_channel = lab[:, :, 0]  # Luminosidade
    s_channel = hsv[:, :, 1]  # Saturação

    # 3. Hipótese H1: Colônias têm alta luminosidade e baixa saturação
    # Ágar amarelado tem alta saturação
    yeast_score = l_channel * (1.0 - s_channel)

    # Normalização local dentro da ROI analisável
    roi_pixels = yeast_score[analyzable_mask > 0]
    if roi_pixels.size > 0 and (roi_pixels.max() - roi_pixels.min()) > 1e-5:
        yeast_score = (yeast_score - roi_pixels.min()) / (roi_pixels.max() - roi_pixels.min())
        yeast_score = np.clip(yeast_score, 0.0, 1.0)

    # 4. Subtração Morfológica de Fundo (Top-Hat Transform)
    # Remove gradientes contínuos de iluminação
    kernel_size = 2 * tophat_radius_px + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    score_uint8 = (yeast_score * 255.0).astype(np.uint8)
    tophat = cv2.morphologyEx(score_uint8, cv2.MORPH_TOPHAT, kernel)

    # Mascara apenas a área útil da placa
    tophat = cv2.bitwise_and(tophat, tophat, mask=analyzable_mask)

    return tophat.astype(np.float32) / 255.0


def segment_colonies_watershed(
    score_f32: np.ndarray,
    analyzable_mask: np.ndarray,
    detection_threshold: float = 0.20,
    peak_min_distance_px: int = 5,
) -> np.ndarray:
    """
    Aplica binarização, transformada de distância euclidiana e Watershed
    com marcadores para desmembrar colônias que se tocam.
    """
    # 1. Binarização adaptativa / thresholding
    binary = (score_f32 >= detection_threshold).astype(np.uint8) * 255
    binary = cv2.bitwise_and(binary, binary, mask=analyzable_mask)

    # Limpeza de ruído pontual fino (abertura morfológica)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)

    if np.count_nonzero(binary) == 0:
        return np.zeros(score_f32.shape, dtype=np.int32)

    # 2. Transformada de Distância Euclidiana
    dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

    # 3. Extração de Marcadores Únicos (Centros das Colônias)
    # Picos locais na distância euclidiana
    # Usando filtro de máximo local do scipy para robustez
    local_max = ndi.maximum_filter(dist_transform, size=peak_min_distance_px) == dist_transform
    peaks = local_max & (dist_transform > 0.25 * dist_transform.max()) & (binary > 0)

    # Rotulação das componentes conexas dos picos
    markers, num_markers = ndi.label(peaks)

    if num_markers == 0:
        return np.zeros(score_f32.shape, dtype=np.int32)

    # 4. Algoritmo Watershed
    # Inverte a distância para criar vales nos centros das colônias
    dist_inv = (dist_transform.max() - dist_transform).astype(np.float32)
    # Watershed do OpenCV requer imagem BGR de 3 canais e marcadores int32
    img_for_ws = np.repeat((score_f32 * 255.0).astype(np.uint8)[:, :, np.newaxis], 3, axis=2)
    markers_ws = markers.astype(np.int32)

    cv2.watershed(img_for_ws, markers_ws)

    # Marcadores de fronteira (-1) são zerados
    markers_ws[markers_ws <= 0] = 0
    markers_ws[binary == 0] = 0

    return markers_ws


def extract_colony_features(
    labeled_mask: np.ndarray,
    gray_image: np.ndarray,
    min_area_px: int = 12,
    max_area_px: int = 15000,
    min_circularity: float = 0.40,
    min_solidity: float = 0.70,
) -> List[SingleColony]:
    """Extrai características morfométricas de cada colônia rotulada e filtra artefatos."""
    colonies: List[SingleColony] = []
    unique_labels = np.unique(labeled_mask)

    colony_counter = 1
    for label_id in unique_labels:
        if label_id == 0:
            continue

        component_mask = (labeled_mask == label_id).astype(np.uint8)
        area = int(np.count_nonzero(component_mask))

        if area < min_area_px or area > max_area_px:
            continue

        # Extração de contorno
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        cnt = contours[0]
        perimeter = float(cv2.arcLength(cnt, True))
        if perimeter <= 0:
            continue

        # Métrica de circularidade: 4 * pi * Area / Perimeter^2
        circularity = float((4.0 * np.pi * area) / (perimeter ** 2))
        circularity = min(1.0, max(0.0, circularity))

        if circularity < min_circularity:
            continue

        # Métrica de solidez: Area / ConvexHull Area
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area / hull_area) if hull_area > 0 else 0.0
        solidity = min(1.0, max(0.0, solidity))

        if solidity < min_solidity:
            continue

        # Centroides (Momentos)
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = float(M["m10"] / M["m00"])
        cy = float(M["m01"] / M["m00"])

        # Intensidade média
        mean_val = float(cv2.mean(gray_image, mask=component_mask)[0])

        colonies.append(
            SingleColony(
                colony_id=colony_counter,
                centroid_x_px=round(cx, 2),
                centroid_y_px=round(cy, 2),
                area_px=area,
                circularity=round(circularity, 4),
                solidity=round(solidity, 4),
                mean_intensity=round(mean_val, 2),
                is_manual_override=False,
            )
        )
        colony_counter += 1

    return colonies


def run_colony_counting(
    image_bgr: np.ndarray,
    analyzable_mask: np.ndarray,
    inoculated_volume_ml: Optional[float] = None,
    dilution_factor: Optional[float] = None,
    detection_threshold: float = 0.20,
    min_area_px: int = 12,
    min_circularity: float = 0.40,
) -> ColonyCountResult:
    """Pipeline completo de contagem de colônias."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    score_f32 = preprocess_plate_image(image_bgr, analyzable_mask)
    labeled_mask = segment_colonies_watershed(score_f32, analyzable_mask, detection_threshold=detection_threshold)
    colonies = extract_colony_features(
        labeled_mask,
        gray,
        min_area_px=min_area_px,
        min_circularity=min_circularity,
    )

    total = len(colonies)
    is_valid_range = (30 <= total <= 300)

    cfu_per_ml: Optional[float] = None
    if inoculated_volume_ml is not None and dilution_factor is not None:
        if inoculated_volume_ml > 0:
            cfu_per_ml = (float(total) * float(dilution_factor)) / float(inoculated_volume_ml)

    return ColonyCountResult(
        total_colonies_auto=total,
        total_colonies_final=total,
        colonies=colonies,
        inoculated_volume_ml=inoculated_volume_ml,
        dilution_factor=dilution_factor,
        cfu_per_ml=round(cfu_per_ml, 2) if cfu_per_ml is not None else None,
        is_in_valid_counting_range=is_valid_range,
        execution_version="2.1.0",
        random_seed=42,
    )
