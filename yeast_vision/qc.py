"""
Módulo de Controle de Qualidade da Imagem (QC Camada 1)
======================================================
Implementa testes determinísticos de pré-condição: desfoque (Laplaciano),
superexposição, subexposição, resolução mínima e enquadramento da placa.
"""

from typing import Optional, Tuple, List
import cv2
import numpy as np

from yeast_vision.contracts import QCResult, QCStatus


def calculate_blur_laplacian(gray_img: np.ndarray) -> float:
    """Calcula a variância do operador Laplaciano como proxy de nitidez/foco."""
    if gray_img.size == 0:
        return 0.0
    lap = cv2.Laplacian(gray_img, cv2.CV_64F)
    return float(np.var(lap))


def evaluate_image_quality(
    image_bgr: np.ndarray,
    plate_circle: Optional[Tuple[float, float, float]] = None,
    blur_threshold: float = 100.0,
    saturation_threshold_pct: float = 0.05,
    underexposure_threshold_pct: float = 0.10,
    nominal_resolution_px: int = 1200,
) -> QCResult:
    """
    Avalia a qualidade óptica e geométrica da imagem capturada.

    Parameters
    ----------
    image_bgr : np.ndarray
        Imagem carregada no formato BGR ou RGB (uint8).
    plate_circle : tuple of (x, y, r), optional
        Centroide e raio da placa detectada para checar enquadramento.
    blur_threshold : float
        Limiar mínimo de variância do Laplaciano para considerar imagem focada.
    saturation_threshold_pct : float
        Fração máxima permitida de pixels saturados (>= 250).
    underexposure_threshold_pct : float
        Fração máxima permitida de pixels subexpostos (<= 15).
    nominal_resolution_px : int
        Resolução nominal recomendada pelo protocolo fotográfico.

    Returns
    -------
    QCResult
        Resultado estruturado do QC conforme contrato Pydantic.
    """
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("Imagem nula ou vazia fornecida para o módulo de QC.")

    height, width = image_bgr.shape[:2]

    # Conversão para escala de cinza
    if len(image_bgr.shape) == 3:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_bgr.copy()

    # 1. Medição de Desfoque
    blur_score = calculate_blur_laplacian(gray)

    # 2. Histograma de Saturação e Subexposição
    total_pixels = float(gray.size)
    saturated_pixels = int(np.count_nonzero(gray >= 250))
    underexposed_pixels = int(np.count_nonzero(gray <= 15))

    frac_saturated = float(saturated_pixels / total_pixels)
    frac_underexposed = float(underexposed_pixels / total_pixels)

    # 3. Verificação de Enquadramento
    is_fully_visible = True
    rejection_reasons: List[str] = []

    if plate_circle is not None:
        cx, cy, r = plate_circle
        # Verifica se o círculo físico da placa ultrapassa os limites da imagem
        margin = 2.0  # tolerância de 2 pixels
        if (cx - r < -margin) or (cy - r < -margin) or (cx + r > width + margin) or (cy + r > height + margin):
            is_fully_visible = False
            rejection_reasons.append("QC_PLATE_CLIPPED")

    # 4. Verificação de Resolução
    if min(width, height) < nominal_resolution_px:
        rejection_reasons.append("QC_LOW_RESOLUTION_WARNING")

    # 5. Avaliação dos Limiares Ópticos
    if blur_score < blur_threshold:
        rejection_reasons.append("QC_BLUR_EXCESSIVE")

    if frac_saturated > saturation_threshold_pct:
        rejection_reasons.append("QC_SATURATION_HIGH")

    if frac_underexposed > underexposure_threshold_pct and is_fully_visible:
        # Só alerta subexposição se não for fundo preto externo
        rejection_reasons.append("QC_UNDEREXPOSURE_WARNING")

    # 6. Determinação do Status Consolidado
    if "QC_PLATE_CLIPPED" in rejection_reasons or blur_score < (blur_threshold * 0.2):
        status = QCStatus.REJECTED_UNQUANTIFIABLE
    elif len(rejection_reasons) > 0:
        status = QCStatus.WARNING_REVIEW_REQUIRED
    else:
        status = QCStatus.PASSED

    return QCResult(
        status=status,
        blur_score_laplacian=round(blur_score, 2),
        fraction_saturated_pixels=round(frac_saturated, 4),
        fraction_underexposed_pixels=round(frac_underexposed, 4),
        resolution_width_px=width,
        resolution_height_px=height,
        is_plate_fully_visible=is_fully_visible,
        rejection_reasons=rejection_reasons,
    )
