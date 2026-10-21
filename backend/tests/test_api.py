import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DocuMind AI Backend"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "DocuMind" in response.json()["project"]

def test_list_schemas_endpoint():
    response = client.get("/api/v1/extractions/schemas")
    assert response.status_code == 200
    data = response.json()
    assert "project_proposal" in data
    assert "contract_agreement" in data
    assert "universal_document" in data

def test_create_and_list_conversations():
    res = client.post("/api/v1/conversations", json={"title": "Q3 Analysis Chat"})
    assert res.status_code == 201
    conv_id = res.json()["id"]

    list_res = client.get("/api/v1/conversations")
    assert list_res.status_code == 200
    conv_ids = [c["id"] for c in list_res.json()]
    assert conv_id in conv_ids
