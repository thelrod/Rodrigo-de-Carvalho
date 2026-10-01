import pytest
from fastapi.testclient import TestClient
from api.server import app
import numpy as np
import cv2
import io
import base64

client = TestClient(app)

@pytest.fixture
def synthetic_plate_image():
    """Gera uma placa sintética reprodutível com 4 colônias"""
    np.random.seed(42)
    img = np.zeros((600, 600, 3), dtype=np.uint8)

    # Fundo escuro
    img[:] = 50

    # Desenha borda da placa de forma mais nítida
    cv2.circle(img, (300, 300), 250, (150, 150, 150), 2)

    # Desenha 4 colônias bem definidas, brilhantes e largas para evitar super segmentação e ruído
    colony_centers = [(200, 200), (250, 250), (350, 350), (400, 400)]
    for center in colony_centers:
        cv2.circle(img, center, 12, (255, 255, 255), -1)

    # Ruído muito leve só para o laplaciano (nitidez)
    noise = np.random.normal(0, 5, (600, 600, 3)).astype(np.uint8)
    img = cv2.add(img, noise)

    # Usa PNG para evitar ruído de compressão JPEG que causa sobre segmentação no Watershed
    success, encoded_image = cv2.imencode('.png', img)
    assert success
    return encoded_image.tobytes()


def test_qc_endpoint(synthetic_plate_image):
    response = client.post("/api/v1/qc", files={"file": ("test.jpg", synthetic_plate_image, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "blur_score_laplacian" in data


def test_colony_count_endpoint(synthetic_plate_image):
    response = client.post(
        "/api/v1/colony-count",
        files={"file": ("test.jpg", synthetic_plate_image, "image/jpeg")},
        data={"medium": "YPD", "strain_id": "test", "plate_id": "test_01", "inoc_vol": 0.1, "dil_factor": 1000}
    )
    assert response.status_code == 200
    data = response.json()

    result = data["result"]
    assert result["total_colonies_final"] == 4
    assert result["cfu_per_ml"] == pytest.approx(40000.0, rel=1e-2)
    assert result["is_in_valid_counting_range"] is False

    # Base64 image decoding verification
    b64_img_str = data["annotated_image_base64"]
    img_bytes = base64.b64decode(b64_img_str)
    assert len(img_bytes) > 1024  # > 1KB

    # CSV data verification
    csv_data = data["csv_data"]
    assert "cfu_per_ml" in csv_data


def test_spot_assay_endpoint(synthetic_plate_image):
    response = client.post(
        "/api/v1/spot-assay",
        files={"file": ("test.jpg", synthetic_plate_image, "image/jpeg")},
        data={"medium": "YPD", "strain_id": "test", "plate_id": "test_01", "grid_rows": 4, "grid_cols": 6}
    )
    assert response.status_code == 200
    data = response.json()

    result = data["result"]
    assert result["grid_rows"] == 4
    assert result["grid_cols"] == 6
    assert len(result["max_dilution_with_growth_by_strain"]) >= 0


def test_invalid_image_upload_returns_400():
    bad_bytes = b"not an image"
    response = client.post("/api/v1/qc", files={"file": ("bad.jpg", bad_bytes, "image/jpeg")})
    assert response.status_code == 400


def test_invalid_medium_returns_422(synthetic_plate_image):
    response = client.post(
        "/api/v1/colony-count",
        files={"file": ("test.jpg", synthetic_plate_image, "image/jpeg")},
        data={"medium": "MEIO_INEXISTENTE", "strain_id": "test", "plate_id": "test_01"}
    )
    assert response.status_code == 422
