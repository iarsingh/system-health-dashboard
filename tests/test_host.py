from fastapi.testclient import TestClient

from healthdash.main import app


def test_host_snapshot_has_disk_and_load():
    client = TestClient(app)
    body = client.get("/host").json()
    assert 0 <= body["disk_used_percent"] <= 100
    assert "load_1m" in body
    assert isinstance(body["alerts"], list)
    assert client.get("/healthz").json()["status"] == "ok"
