"""
Testes unitários para o módulo de exportação e anotação visual (app.exporter).
"""

from datetime import datetime
import numpy as np
import cv2

from yeast_vision.contracts import (
    MediumType,
    ExperimentType,
    QCStatus,
    ImageMetadata,
    QCResult,
    ColonyCountResult,
    SingleColony,
    SpotAssayResult,
    SingleSpotMeasurement,
    PlateROIResult,
)
from app.exporter import (
    export_colony_count_csv,
    export_spot_assay_csv,
    create_annotated_colony_image,
    create_annotated_spot_image,
)


def test_export_colony_count_csv():
    meta = ImageMetadata(
        image_id="img_001",
        filename="test_plate.jpg",
        timestamp_capture=datetime.now(),
        medium=MediumType.YPD,
        strain_id="BY4741",
        plate_id="PLATE_A",
        experiment_type=ExperimentType.COLONY_COUNT,
    )
    qc = QCResult(
        status=QCStatus.PASSED,
        blur_score_laplacian=180.5,
        fraction_saturated_pixels=0.01,
        fraction_underexposed_pixels=0.02,
        resolution_width_px=1200,
        resolution_height_px=1200,
        is_plate_fully_visible=True,
    )
    count_res = ColonyCountResult(
        total_colonies_auto=2,
        total_colonies_final=2,
        colonies=[
            SingleColony(
                colony_id=1,
                centroid_x_px=120.5,
                centroid_y_px=150.2,
                area_px=45,
                circularity=0.88,
                solidity=0.92,
                mean_intensity=190.0,
            ),
            SingleColony(
                colony_id=2,
                centroid_x_px=220.0,
                centroid_y_px=250.0,
                area_px=60,
                circularity=0.85,
                solidity=0.90,
                mean_intensity=175.0,
            ),
        ],
        inoculated_volume_ml=0.1,
        dilution_factor=1000.0,
        cfu_per_ml=20000.0,
        is_in_valid_counting_range=False,
    )

    csv_text = export_colony_count_csv(meta, qc, count_res)
    assert "centroid_x_px" in csv_text
    assert "cfu_per_ml" in csv_text
    assert "BY4741" in csv_text
    assert "20000.0" in csv_text


def test_export_spot_assay_csv():
    meta = ImageMetadata(
        image_id="img_002",
        filename="spot_test.jpg",
        timestamp_capture=datetime.now(),
        medium=MediumType.YPGAL,
        stressor="LiCl",
        stressor_concentration_mM=20.0,
        strain_id="W303",
        plate_id="PLATE_B",
        experiment_type=ExperimentType.SPOT_ASSAY,
    )
    qc = QCResult(
        status=QCStatus.WARNING_REVIEW_REQUIRED,
        blur_score_laplacian=95.0,
        fraction_saturated_pixels=0.03,
        fraction_underexposed_pixels=0.05,
        resolution_width_px=800,
        resolution_height_px=800,
        is_plate_fully_visible=True,
        rejection_reasons=["QC_LOW_RESOLUTION_WARNING"],
    )
    spot_res = SpotAssayResult(
        grid_rows=1,
        grid_cols=2,
        spots=[
            SingleSpotMeasurement(
                row_idx=0,
                col_idx=0,
                strain_id="W303",
                dilution_factor=1.0,
                growth_detected=True,
                area_growth_px=250,
                background_corrected_signal=1200.5,
                is_saturated=False,
                confidence_score=0.95,
            ),
            SingleSpotMeasurement(
                row_idx=0,
                col_idx=1,
                strain_id="W303",
                dilution_factor=10.0,
                growth_detected=False,
                area_growth_px=0,
                background_corrected_signal=0.0,
                is_saturated=False,
                confidence_score=0.85,
            ),
        ],
        max_dilution_with_growth_by_strain={"W303": 1.0},
    )

    csv_text = export_spot_assay_csv(meta, qc, spot_res)
    assert "background_corrected_signal_au" in csv_text
    assert "1200.5" in csv_text
    assert "LiCl" in csv_text


def test_annotated_images_generation():
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    roi = PlateROIResult(
        center_x_px=200.0,
        center_y_px=200.0,
        radius_px=180.0,
        exclusion_margin_pct=8.0,
        analyzable_area_px=90000,
        excluded_peripheral_area_px=11000,
    )
    count_res = ColonyCountResult(
        total_colonies_auto=1,
        total_colonies_final=1,
        colonies=[
            SingleColony(
                colony_id=1,
                centroid_x_px=200.0,
                centroid_y_px=200.0,
                area_px=50,
                circularity=0.9,
                solidity=0.95,
                mean_intensity=200.0,
            )
        ],
        is_in_valid_counting_range=False,
    )
    spot_res = SpotAssayResult(
        grid_rows=1,
        grid_cols=1,
        spots=[
            SingleSpotMeasurement(
                row_idx=0,
                col_idx=0,
                strain_id="WT",
                dilution_factor=1.0,
                growth_detected=True,
                area_growth_px=100,
                background_corrected_signal=500.0,
                is_saturated=False,
                confidence_score=0.95,
            )
        ],
        max_dilution_with_growth_by_strain={"WT": 1.0},
    )

    ann_col = create_annotated_colony_image(img, roi, count_res)
    assert ann_col.shape == img.shape

    ann_spot = create_annotated_spot_image(img, roi, [(0, 0, (50, 50, 150, 150))], spot_res)
    assert ann_spot.shape == img.shape
