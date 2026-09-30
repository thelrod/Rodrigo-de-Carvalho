"""
Testes unitários da detecção da placa de Petri e ROI.
"""

import numpy as np
import cv2
import pytest

from yeast_vision.plate import detect_petri_dish


def test_detect_petri_dish_synthetic():
    # Cria uma imagem sintética com fundo preto e disco cinza/amarelado (placa)
    img = np.zeros((800, 800, 3), dtype=np.uint8)
    center = (400, 400)
    radius = 320
    # Placa
    cv2.circle(img, center, radius, (80, 180, 200), -1)

    roi, mask = detect_petri_dish(img, exclusion_margin_pct=10.0)

    # Verifica se detectou o centroide próximo a (400, 400)
    assert abs(roi.center_x_px - 400) < 15
    assert abs(roi.center_y_px - 400) < 15
    # Verifica raio aproximado de 320
    assert abs(roi.radius_px - 320) < 20

    # Verifica margem adaptativa de 10%
    expected_inner_radius = 320 * 0.90
    expected_area = np.pi * (expected_inner_radius ** 2)
    assert abs(roi.analyzable_area_px - expected_area) / expected_area < 0.10

    # Máscara binária deve ser uint8 com 255 no centro e 0 no canto
    assert mask[400, 400] == 255
    assert mask[10, 10] == 0


def test_detect_petri_dish_adaptive_meniscus():
    img = np.zeros((800, 800, 3), dtype=np.uint8)
    cv2.circle(img, (400, 400), 300, (100, 150, 180), -1)

    roi, mask = detect_petri_dish(img, auto_margin=True)
    # A margem adaptativa deve ficar em uma faixa biológica plausível (5% a 12%)
    assert 5.0 <= roi.exclusion_margin_pct <= 12.0
    assert roi.analyzable_area_px > 0
