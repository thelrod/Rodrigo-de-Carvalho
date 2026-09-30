from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64
import time
from datetime import datetime

from yeast_vision.contracts import (
    MediumType,
    ExperimentType,
    ImageMetadata,
    QCResult,
    QCStatus
)
from yeast_vision.qc import evaluate_image_quality
from yeast_vision.plate import detect_petri_dish
from yeast_vision.colony import run_colony_counting
from yeast_vision.spot import run_spot_assay_analysis, detect_grid_cells
from app.exporter import (
    export_colony_count_csv,
    export_spot_assay_csv,
    create_annotated_colony_image,
    create_annotated_spot_image,
)

app = FastAPI(title="YeastPlate Analyzer API")

def _read_image(file: UploadFile) -> np.ndarray:
    try:
        contents = file.file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image format.")
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {e}")

def _encode_image_base64(img: np.ndarray) -> str:
    success, encoded_image = cv2.imencode('.png', img)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode annotated image.")
    return base64.b64encode(encoded_image).decode('utf-8')

def _create_metadata(filename: str, experiment_type: ExperimentType, medium: str, strain_id: str, plate_id: str) -> ImageMetadata:
     return ImageMetadata(
        image_id=f"IMG_{int(time.time())}",
        filename=filename,
        timestamp_capture=datetime.now(),
        medium=MediumType(medium),
        carbon_source_concentration_pct=2.0,
        stressor=None,
        stressor_concentration_mM=None,
        strain_id=strain_id,
        plate_id=plate_id,
        experiment_type=experiment_type,
        partition="analysis_session",
    )

@app.post("/api/v1/qc")
async def api_qc(
    file: UploadFile = File(...)
):
    image_bgr = _read_image(file)
    plate_roi, _ = detect_petri_dish(image_bgr, auto_margin=True)
    qc = evaluate_image_quality(
        image_bgr,
        plate_circle=(plate_roi.center_x_px, plate_roi.center_y_px, plate_roi.radius_px),
    )
    return qc.model_dump()


@app.post("/api/v1/colony-count")
async def api_colony_count(
    file: UploadFile = File(...),
    medium: str = Form("YPD"),
    strain_id: str = Form("BY4741"),
    plate_id: str = Form("PLACA_01"),
    inoc_vol: float = Form(0.10),
    dil_factor: float = Form(1000.0)
):
    image_bgr = _read_image(file)
    plate_roi, mask = detect_petri_dish(image_bgr, auto_margin=True)
    qc = evaluate_image_quality(
        image_bgr,
        plate_circle=(plate_roi.center_x_px, plate_roi.center_y_px, plate_roi.radius_px),
    )

    count_res = run_colony_counting(
        image_bgr,
        mask,
        inoculated_volume_ml=inoc_vol,
        dilution_factor=dil_factor,
        detection_threshold=0.20,
        min_area_px=None,
        plate_radius_px=plate_roi.radius_px,
    )

    annotated_img = create_annotated_colony_image(image_bgr, plate_roi, count_res)
    b64_img = _encode_image_base64(annotated_img)

    metadata = _create_metadata(file.filename or "upload.jpg", ExperimentType.COLONY_COUNT, medium, strain_id, plate_id)
    csv_data = export_colony_count_csv(metadata, qc, count_res)

    return JSONResponse(content={
        "qc": qc.model_dump(),
        "result": count_res.model_dump(),
        "annotated_image_base64": b64_img,
        "csv_data": csv_data
    })


@app.post("/api/v1/spot-assay")
async def api_spot_assay(
    file: UploadFile = File(...),
    medium: str = Form("YPD"),
    strain_id: str = Form("BY4741"),
    plate_id: str = Form("PLACA_01"),
    grid_rows: int = Form(4),
    grid_cols: int = Form(6)
):
    image_bgr = _read_image(file)
    plate_roi, mask = detect_petri_dish(image_bgr, auto_margin=True)
    qc = evaluate_image_quality(
        image_bgr,
        plate_circle=(plate_roi.center_x_px, plate_roi.center_y_px, plate_roi.radius_px),
    )

    spot_res = run_spot_assay_analysis(image_bgr, mask, grid_rows=grid_rows, grid_cols=grid_cols)
    spot_cells = detect_grid_cells(image_bgr, mask, grid_rows=grid_rows, grid_cols=grid_cols)

    annotated_spot = create_annotated_spot_image(image_bgr, plate_roi, spot_cells, spot_res)
    b64_img = _encode_image_base64(annotated_spot)

    metadata = _create_metadata(file.filename or "upload.jpg", ExperimentType.SPOT_ASSAY, medium, strain_id, plate_id)
    csv_data = export_spot_assay_csv(metadata, qc, spot_res)

    return JSONResponse(content={
        "qc": qc.model_dump(),
        "result": spot_res.model_dump(),
        "annotated_image_base64": b64_img,
        "csv_data": csv_data
    })
