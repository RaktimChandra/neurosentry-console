"""Smoke-test the HTTP API with FastAPI's TestClient."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    # Trigger lifespan events
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_system(client):
    r = client.get("/api/system")
    assert r.status_code == 200
    data = r.json()
    assert "torch" in data
    assert data["fs"] == 128


def test_patients_list(client):
    r = client.get("/api/patients")
    assert r.status_code == 200
    data = r.json()
    assert len(data["patients"]) >= 3
    for p in data["patients"]:
        assert "id" in p and "label" in p


def test_patient_meta(client):
    r = client.get("/api/patients/p05")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "p05"
    assert data["n_samples"] > 100


def test_patient_404(client):
    r = client.get("/api/patients/nonexistent")
    assert r.status_code == 404


def test_metrics(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["hybrid"]["test"]["accuracy"] >= 0.9
    assert data["baseline"]["test"]["accuracy"] >= 0.9


def test_infer_window(client):
    # Random window
    import numpy as np
    window = np.random.randn(512).tolist()
    r = client.post("/api/infer/window", json={"samples": window})
    assert r.status_code == 200
    data = r.json()
    assert len(data["probs"]) == 3
    assert data["class_name"] in ["interictal", "preictal", "ictal"]
    assert 0 <= data["confidence"] <= 1


def test_infer_patient_window(client):
    r = client.get("/api/infer/patient/p05/window/5")
    assert r.status_code == 200
    data = r.json()
    assert "class_name" in data
    assert "ground_truth" in data
