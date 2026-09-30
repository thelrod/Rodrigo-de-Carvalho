"""
Testes de integração e regressão sobre as imagens reais de bancada da UFRJ.
(SAMPLE_YPD_300mM_LiCl.jpg e SAMPLE_YPGAL_20mM_LiCl.jpg)
"""

import os
import cv2
import pytest

from yeast_vision.qc import evaluate_image_quality
from yeast_vision.plate import detect_petri_dish
from yeast_vision.spot import run_spot_assay_analysis
from yeast_vision.contracts import QCStatus

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "reference_dataset", "raw")
YPD_IMG_PATH = os.path.join(RAW_DIR, "SAMPLE_YPD_300mM_LiCl.jpg")
YPGAL_IMG_PATH = os.path.join(RAW_DIR, "SAMPLE_YPGAL_20mM_LiCl.jpg")


def test_real_plate_ypd_pipeline():
    assert os.path.exists(YPD_IMG_PATH), f"Imagem {YPD_IMG_PATH} não encontrada."
    img = cv2.imread(YPD_IMG_PATH)
    assert img is not None

    # 1. Detecção da Placa
    roi, mask = detect_petri_dish(img, exclusion_margin_pct=8.0)
    assert roi.radius_px > 100.0
    assert roi.analyzable_area_px > 50000

    # 2. Avaliação de QC
    qc = evaluate_image_quality(img, plate_circle=(roi.center_x_px, roi.center_y_px, roi.radius_px))
    # A imagem tem 460x1024, então deve disparar QC_LOW_RESOLUTION_WARNING sem quebrar o schema
    assert "QC_LOW_RESOLUTION_WARNING" in qc.rejection_reasons
    assert qc.resolution_width_px == 460
    assert qc.resolution_height_px == 1024

    # 3. Execução do Spot Assay (grade 4x6 conforme visto na placa)
    res = run_spot_assay_analysis(img, mask, grid_rows=4, grid_cols=6)
    assert res.grid_rows == 4
    assert res.grid_cols == 6
    assert len(res.spots) == 24

    # Deve detectar crescimento em múltiplos spots
    spots_com_crescimento = [s for s in res.spots if s.growth_detected]
    assert len(spots_com_crescimento) >= 5

    # Nenhum sinal integrado deve ser negativo ou infinito
    for s in res.spots:
        assert s.background_corrected_signal >= 0.0


def test_real_plate_ypgal_pipeline():
    assert os.path.exists(YPGAL_IMG_PATH), f"Imagem {YPGAL_IMG_PATH} não encontrada."
    img = cv2.imread(YPGAL_IMG_PATH)
    assert img is not None

    # 1. Detecção da Placa
    roi, mask = detect_petri_dish(img, exclusion_margin_pct=8.0)
    assert roi.radius_px > 100.0
    assert roi.analyzable_area_px > 50000

    # 2. Avaliação de QC
    qc = evaluate_image_quality(img, plate_circle=(roi.center_x_px, roi.center_y_px, roi.radius_px))
    assert qc.resolution_width_px == 460
    assert qc.resolution_height_px == 1024

    # 3. Execução do Spot Assay (grade 4x6)
    res = run_spot_assay_analysis(img, mask, grid_rows=4, grid_cols=6)
    assert len(res.spots) == 24

    # Deve haver spots com crescimento
    spots_com_crescimento = [s for s in res.spots if s.growth_detected]
    assert len(spots_com_crescimento) >= 5
