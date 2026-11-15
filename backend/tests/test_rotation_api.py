from fastapi.testclient import TestClient

from cropwise_climate.api import app

client = TestClient(app)


def test_rotation_compare_success():
    response = client.post(
        "/api/rotation/compare",
        json={"region_id": "punjab_ludhiana", "rotation_id": "base"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["result"]["scores"]["water"] == 30.0
    assert body["result"]["scores"]["climate_resilience"] == 40.0
    assert body["result"]["overall"] == 34.0
    assert body["result"]["confidence"] == "low"
    assert body["result"]["needs_expert_review"] is True
    assert body["result"]["scores"]["soil_health"] is None
    assert len(body["crop_evidence"]) == 2


def test_rotation_compare_unknown_region():
    response = client.post(
        "/api/rotation/compare",
        json={"region_id": "unknown_region", "rotation_id": "base"},
    )
    assert response.status_code == 404


def test_rotation_compare_unknown_rotation():
    response = client.post(
        "/api/rotation/compare",
        json={"region_id": "punjab_ludhiana", "rotation_id": "unknown"},
    )
    assert response.status_code == 404


def test_rotation_compare_missing_fields():
    response = client.post(
        "/api/rotation/compare",
        json={"region_id": "punjab_ludhiana"},
    )
    assert response.status_code == 422
