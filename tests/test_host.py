from fastapi.testclient import TestClient

from healthdash.host import HISTORY, evaluate, level, parse_meminfo, prometheus
from healthdash.main import app

client = TestClient(app)

MEMINFO = """MemTotal:       16000000 kB
MemFree:         1000000 kB
MemAvailable:    4000000 kB
"""


def readings(**overrides):
    base = {"load_1m": 1.0, "cpu_count": 4, "memory_used_percent": 50.0, "disks": {"/": 40.0}}
    base.update(overrides)
    return base


def test_meminfo_uses_available_not_free():
    assert parse_meminfo(MEMINFO) == 75.0


def test_meminfo_without_available_is_unknown():
    assert parse_meminfo("MemTotal: 100 kB\nMemFree: 10 kB\n") is None


def test_levels_at_the_boundaries():
    assert level(79.9) == "ok"
    assert level(80) == "warn"
    assert level(90) == "critical"
    assert level(None) == "unknown"


def test_load_is_judged_per_cpu():
    body = evaluate(readings(load_1m=3.6, cpu_count=4))
    assert body["load_percent"] == 90.0
    assert body["checks"]["load"] == "critical"
    assert body["status"] == "critical"


def test_one_full_disk_makes_the_host_critical():
    body = evaluate(readings(disks={"/": 40.0, "/data": 95.0}))
    assert body["checks"]["disk:/data"] == "critical"
    assert "disk:/data is critical" in body["alerts"]


def test_unknown_memory_does_not_raise_an_alert():
    body = evaluate(readings(memory_used_percent=None))
    assert body["checks"]["memory"] == "unknown"
    assert body["status"] == "ok"


def test_unreadable_load_is_unknown():
    body = evaluate(readings(load_1m=None))
    assert body["load_percent"] is None
    assert body["checks"]["load"] == "unknown"
    assert "host_load_1m" not in prometheus(body)


def test_prometheus_text_names_each_mount():
    text = prometheus(evaluate(readings(disks={"/": 40.0, "/data": 95.0})))
    assert 'host_disk_used_percent{mount="/data"} 95.0' in text
    assert "host_status_critical 1" in text


def test_live_host_endpoint_and_history():
    HISTORY.clear()
    body = client.get("/host").json()
    assert 0 <= body["disks"]["/"] <= 100
    assert body["status"] in {"ok", "warn", "critical"}
    assert client.get("/host/history").json()["count"] == 1
    assert client.get("/healthz").json()["status"] == "ok"


def test_missing_mount_is_refused():
    assert client.get("/host", params={"mount": "/does-not-exist"}).status_code == 422


def test_metrics_endpoint_is_plain_text():
    response = client.get("/metrics")
    assert response.headers["content-type"].startswith("text/plain")
    assert "host_disk_used_percent" in response.text
