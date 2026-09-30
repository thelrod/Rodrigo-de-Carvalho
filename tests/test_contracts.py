"""
Testes unitários dos contratos Pydantic v2 do YeastPlate Analyzer.
"""

from datetime import datetime
import pytest
from pydantic import ValidationError

from yeast_vision.contracts import (
    MediumType,
    ExperimentType,
    QCStatus,
    ImageMetadata,
    QCResult,
    PlateROIResult,
    SingleColony,
    ColonyCountResult,
    SingleSpotMeasurement,
    SpotAssayResult,
)


def test_image_metadata_valid():
    meta = ImageMetadata(
        image_id="test_hash_123",
        filename="plate_01.jpg",
        timestamp_capture=datetime.now(),
        medium=MediumType.YPD,
        carbon_source_concentration_pct=2.0,
        stressor="LiCl",
        stressor_concentration_mM=300.0,
        incubation_time_hours=48.0,
        temperature_celsius=30.0,
        strain_id="BY4741",
        plate_id="PLATE_01",
        experiment_type=ExperimentType.SPOT_ASSAY,
        partition="test_frozen",
        operator_id="Rodrigo",
        has_artifacts=False,
    )
    assert meta.medium == MediumType.YPD
    assert meta.stressor_concentration_mM == 300.0
    json_data = meta.model_dump_json()
    assert "test_hash_123" in json_data


def test_image_metadata_invalid_carbon():
    with pytest.raises(ValidationError):
        ImageMetadata(
            image_id="123",
            filename="x.jpg",
            timestamp_capture=datetime.now(),
            medium=MediumType.YPD,
            carbon_source_concentration_pct=50.0,  # Max is 10.0
            strain_id="WT",
            plate_id="P1",
            experiment_type=ExperimentType.COLONY_COUNT,
        )


def test_qc_result_validation():
    qc = QCResult(
        status=QCStatus.PASSED,
        blur_score_laplacian=185.4,
        fraction_saturated_pixels=0.01,
        fraction_underexposed_pixels=0.03,
        resolution_width_px=1920,
        resolution_height_px=1080,
        is_plate_fully_visible=True,
    )
    assert qc.status == QCStatus.PASSED
    assert qc.is_plate_fully_visible is True


def test_colony_count_result_valid_range():
    # Test valid range (30 <= N <= 300)
    res_valid = ColonyCountResult(
        total_colonies_auto=120,
        total_colonies_final=120,
        inoculated_volume_ml=0.1,
        dilution_factor=1000.0,
        cfu_per_ml=1200000.0,
        is_in_valid_counting_range=True,
    )
    assert res_valid.is_in_valid_counting_range is True
    assert res_valid.cfu_per_ml == 1.2e6

    # Test invalid range (N < 30)
    res_low = ColonyCountResult(
        total_colonies_auto=15,
        total_colonies_final=15,
        is_in_valid_counting_range=False,
    )
    assert res_low.is_in_valid_counting_range is False


def test_spot_assay_result():
    spot = SingleSpotMeasurement(
        row_idx=0,
        col_idx=2,
        strain_id="WT",
        dilution_factor=100.0,
        growth_detected=True,
        area_growth_px=450,
        background_corrected_signal=12500.5,
        is_saturated=False,
        confidence_score=0.95,
    )
    assay = SpotAssayResult(
        grid_rows=1,
        grid_cols=3,
        spots=[spot],
        max_dilution_with_growth_by_strain={"WT": 100.0},
    )
    assert assay.max_dilution_with_growth_by_strain["WT"] == 100.0
    assert assay.spots[0].background_corrected_signal == 12500.5
