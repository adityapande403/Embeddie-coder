"""
Integration tests for FastAPI REST service.
"""

from fastapi.testclient import TestClient
from embeddedcoder.api.server import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "EmbeddedCoder AI"


def test_model_info_endpoint():
    response = client.get("/v1/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "EmbeddedCoder-1.5B"
    assert "license" in data
    assert "capabilities" in data


def test_packet_decode_endpoint():
    # Modbus frame: 01 03 00 64 00 02 85 D4 (Slave 1, FC 3, Addr 100, Qty 2)
    response = client.post("/v1/decode-packet", json={
        "protocol": "modbus",
        "hex_bytes": "01030064000285D4"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["protocol"] == "modbus"
    assert "deterministic_fields" in data
    assert data["deterministic_fields"]["slave_id"] == 1
    assert data["deterministic_fields"]["function_code"] == 3
