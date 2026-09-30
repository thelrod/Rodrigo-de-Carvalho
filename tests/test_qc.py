"""
Testes unitários do módulo de Controle de Qualidade (QC Camada 1).
"""

import numpy as np
import cv2
import pytest

from yeast_vision.qc import calculate_blur_laplacian, evaluate_image_quality
from yeast_vision.contracts import QCStatus


def test_blur_laplacian_sharp_vs_blurry():
    # Imagem nítida com bordas de alto contraste
    sharp = np.zeros((500, 500), dtype=np.uint8)
    cv2.circle(sharp, (250, 250), 100, 255, -1)
    for i in range(10, 490, 20):
        cv2.line(sharp, (i, 0), (i, 500), 200, 2)

    # Imagem desfocada com forte blur gaussiano
    blurry = cv2.GaussianBlur(sharp, (31, 31), 10)

    score_sharp = calculate_blur_laplacian(sharp)
    score_blurry = calculate_blur_laplacian(blurry)

    assert score_sharp > score_blurry
    assert score_sharp > 100.0


def test_qc_saturation_flag():
    # Cria imagem com 15% de pixels superexpostos (>= 250)
    img = np.full((600, 600, 3), 100, dtype=np.uint8)
    img[:150, :360] = 255  # 150*360 / 600*600 = 54000 / 360000 = 15%

    qc = evaluate_image_quality(img, saturation_threshold_pct=0.05)
    assert "QC_SATURATION_HIGH" in qc.rejection_reasons
    assert qc.status == QCStatus.WARNING_REVIEW_REQUIRED


def test_qc_plate_clipped_flag():
    # Imagem 600x600, mas a placa tem centroide (100, 100) e raio 200 (ultrapassa borda esquerda e superior)
    img = np.full((600, 600, 3), 100, dtype=np.uint8)
    qc = evaluate_image_quality(img, plate_circle=(100.0, 100.0, 200.0))

    assert qc.is_plate_fully_visible is False
    assert "QC_PLATE_CLIPPED" in qc.rejection_reasons
    assert qc.status == QCStatus.REJECTED_UNQUANTIFIABLE


def test_qc_low_resolution_warning():
    # Imagem 500x500 (abaixo de 1200x1200)
    img = np.full((500, 500, 3), 100, dtype=np.uint8)
    qc = evaluate_image_quality(img, nominal_resolution_px=1200)

    assert "QC_LOW_RESOLUTION_WARNING" in qc.rejection_reasons
