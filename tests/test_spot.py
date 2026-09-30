"""
Testes unitários do motor de Spot Assay (Modo 2).
"""

import numpy as np
import cv2
import pytest

from yeast_vision.spot import detect_grid_cells, measure_spot_cell, run_spot_assay_analysis


def test_spot_assay_synthetic_grid():
    # Cria uma grade sintética 2x3 de gotas com diluição decrescente
    h, w = 600, 600
    img = np.full((h, w, 3), (30, 120, 160), dtype=np.uint8)  # ágar amarelado
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (300, 300), 260, 255, -1)

    # Linha 0 (Linhagem WT): cresce em todas as 3 diluições (1, 10, 100)
    cv2.circle(img, (200, 220), 25, (220, 230, 240), -1)
    cv2.circle(img, (300, 220), 20, (210, 225, 235), -1)
    cv2.circle(img, (400, 220), 15, (200, 220, 230), -1)

    # Linha 1 (Linhagem Sensível): cresce apenas na diluição 1 (morre em 10 e 100)
    cv2.circle(img, (200, 380), 22, (220, 230, 240), -1)
    # diluição 10 e 100 permanecem vazias

    res = run_spot_assay_analysis(
        img,
        mask,
        grid_rows=2,
        grid_cols=3,
        strain_ids=["WT", "Sensivel"],
        dilution_series=[1.0, 10.0, 100.0],
    )

    assert res.grid_rows == 2
    assert res.grid_cols == 3
    assert len(res.spots) == 6

    # Métrica primária: maior diluição com crescimento
    # WT deve atingir 100.0
    assert res.max_dilution_with_growth_by_strain["WT"] == 100.0
    # Sensível deve parar em 1.0
    assert res.max_dilution_with_growth_by_strain["Sensivel"] == 1.0

    # Verifica que sinal integrado do primeiro spot de WT é maior que 0
    spot_0_0 = [s for s in res.spots if s.row_idx == 0 and s.col_idx == 0][0]
    assert spot_0_0.growth_detected is True
    assert spot_0_0.background_corrected_signal > 1000.0

    # Verifica que spot vazio não detecta crescimento
    spot_1_2 = [s for s in res.spots if s.row_idx == 1 and s.col_idx == 2][0]
    assert spot_1_2.growth_detected is False
    assert spot_1_2.background_corrected_signal == 0.0
