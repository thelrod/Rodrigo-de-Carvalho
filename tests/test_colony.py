"""
Testes unitários do motor de contagem de colônias (Modo 1).
"""

import numpy as np
import cv2
import pytest

from yeast_vision.colony import (
    preprocess_plate_image,
    segment_colonies_watershed,
    extract_colony_features,
    run_colony_counting,
)


def test_colony_counting_synthetic_plate():
    # Cria uma placa sintética com 5 colônias bem definidas (3 isoladas, 2 encostadas)
    h, w = 600, 600
    img = np.full((h, w, 3), (40, 140, 180), dtype=np.uint8)  # fundo amarelado
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (300, 300), 250, 255, -1)

    # 3 colônias isoladas
    cv2.circle(img, (200, 200), 15, (230, 240, 245), -1)
    cv2.circle(img, (400, 200), 18, (230, 240, 245), -1)
    cv2.circle(img, (300, 400), 12, (230, 240, 245), -1)

    # 2 colônias encostadas (teste do Watershed)
    cv2.circle(img, (285, 250), 14, (230, 240, 245), -1)
    cv2.circle(img, (305, 250), 14, (230, 240, 245), -1)

    result = run_colony_counting(
        img,
        mask,
        inoculated_volume_ml=0.1,
        dilution_factor=1000.0,
        detection_threshold=0.15,
        min_area_px=10,
    )

    # Deve detectar as 5 colônias (inclusive separando as 2 encostadas pelo watershed)
    assert result.total_colonies_auto >= 4
    assert result.total_colonies_final == result.total_colonies_auto

    # Verifica cálculo de UFC/mL: N * 1000 / 0.1 = N * 10000
    expected_cfu = result.total_colonies_auto * 10000.0
    assert result.cfu_per_ml == expected_cfu

    # Verifica morfometria de uma colônia isolada
    for col in result.colonies:
        assert col.circularity > 0.40
        assert col.solidity > 0.70
        assert col.area_px > 10
