from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_mock_payload():
    """Creates a mock, valid payload for testing."""
    tiny_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    mock_landmarks = [{"x": 0.5, "y": 0.5} for _ in range(68)]

    return {
        "image": tiny_image_b64,
        "landmarks": mock_landmarks,
        "segmentation_map": tiny_image_b64
    }

def test_submit_job_with_correct_payload():
    """
    Tests that the API successfully accepts a job with a correct payload.
    """
    payload = get_mock_payload()
    response = client.post("/api/v1/submit", json=payload)

    assert response.status_code == 202

    data = response.json()
    assert "id" in data
    assert "status" in data
    assert data["status"] == "pending"

def test_submit_job_with_invalid_payload():
    """
    Tests that the API rejects a job with a missing field and returns a 422 error.
    """
    invalid_payload = {
        "image": "test_string",
        "segmentation_map": "test_string"
    }
    response = client.post("/api/v1/submit", json=invalid_payload)
    assert response.status_code == 422
