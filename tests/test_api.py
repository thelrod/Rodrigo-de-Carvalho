from fastapi.testclient import TestClient
from api.server import app
import numpy as np
import cv2
import io

client = TestClient(app)

def create_synthetic_image():
    # Crie uma imagem preta de 600x600 (válida para os testes)
    img = np.zeros((600, 600, 3), dtype=np.uint8)

    # Desenhe uma borda de placa de Petri
    cv2.circle(img, (300, 300), 250, (150, 150, 150), 2)

    # Adicione colônias espalhadas pela placa, bem visíveis e nítidas, para passar no QC de laplaciano e area mínima
    cv2.circle(img, (200, 200), 8, (255, 255, 255), -1)
    cv2.circle(img, (250, 250), 8, (255, 255, 255), -1)
    cv2.circle(img, (350, 350), 8, (255, 255, 255), -1)
    cv2.circle(img, (400, 400), 8, (255, 255, 255), -1)

    # Adicione alguma textura (ruído) ao fundo para que a variância laplaciana (nitidez) seja alta
    noise = np.random.normal(0, 30, (600, 600, 3)).astype(np.uint8)
    img = cv2.add(img, noise)

    success, encoded_image = cv2.imencode('.jpg', img)
    assert success
    return io.BytesIO(encoded_image.tobytes())

def test_qc_endpoint():
    file = create_synthetic_image()
    response = client.post("/api/v1/qc", files={"file": ("test.jpg", file, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "blur_score_laplacian" in data

def test_colony_count_endpoint():
    file = create_synthetic_image()
    response = client.post(
        "/api/v1/colony-count",
        files={"file": ("test.jpg", file, "image/jpeg")},
        data={"medium": "YPD", "strain_id": "test", "plate_id": "test_01", "inoc_vol": 0.1, "dil_factor": 1000}
    )
    assert response.status_code == 200
    data = response.json()
    assert "qc" in data
    assert "result" in data
    assert "cfu_per_ml" in data["result"]
    assert "is_in_valid_counting_range" in data["result"]
    assert "annotated_image_base64" in data
    assert "csv_data" in data

def test_spot_assay_endpoint():
    file = create_synthetic_image()
    response = client.post(
        "/api/v1/spot-assay",
        files={"file": ("test.jpg", file, "image/jpeg")},
        data={"medium": "YPD", "strain_id": "test", "plate_id": "test_01", "grid_rows": 4, "grid_cols": 6}
    )
    assert response.status_code == 200
    data = response.json()
    assert "qc" in data
    assert "result" in data
    assert "max_dilution_with_growth_by_strain" in data["result"]
    assert "annotated_image_base64" in data
    assert "csv_data" in data
