import os
import shutil
from collections import deque
from datetime import datetime, timezone

WARN_PERCENT = float(os.environ.get("HEALTH_WARN_PERCENT", "80"))
CRITICAL_PERCENT = float(os.environ.get("HEALTH_CRITICAL_PERCENT", "90"))
HISTORY = deque(maxlen=int(os.environ.get("HEALTH_HISTORY", "60")))


def parse_meminfo(text):
    values = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        parts = raw.strip().split()
        if parts and parts[0].isdigit():
            values[key] = int(parts[0])
    total = values.get("MemTotal") or 0
    available = values.get("MemAvailable")
    if total <= 0 or available is None:
        return None
    return round((total - available) / total * 100, 1)


def memory_percent(path="/proc/meminfo"):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return parse_meminfo(handle.read())


def disk_percent(path):
    usage = shutil.disk_usage(path)
    return round(usage.used / usage.total * 100, 1)


def level(percent, warn=WARN_PERCENT, critical=CRITICAL_PERCENT):
    if percent is None:
        return "unknown"
    if percent >= critical:
        return "critical"
    if percent >= warn:
        return "warn"
    return "ok"


def evaluate(readings, warn=WARN_PERCENT, critical=CRITICAL_PERCENT):
    cpu_count = max(1, readings["cpu_count"])
    load = readings["load_1m"]
    load_percent = None if load is None else round(load / cpu_count * 100, 1)
    checks = {
        "load": level(load_percent, warn, critical),
        "memory": level(readings["memory_used_percent"], warn, critical),
    }
    for mount, percent in readings["disks"].items():
        checks[f"disk:{mount}"] = level(percent, warn, critical)
    alerts = [f"{name} is {state}" for name, state in checks.items() if state in {"warn", "critical"}]
    if "critical" in checks.values():
        status = "critical"
    elif "warn" in checks.values():
        status = "warn"
    else:
        status = "ok"
    return {
        **readings,
        "load_percent": load_percent,
        "checks": checks,
        "status": status,
        "alerts": alerts,
        "thresholds": {"warn": warn, "critical": critical},
    }


def load_1m():
    try:
        return round(os.getloadavg()[0], 2)
    except OSError:
        return None


def read_host(mounts=("/",)):
    return {
        "load_1m": load_1m(),
        "cpu_count": os.cpu_count() or 1,
        "memory_used_percent": memory_percent(),
        "disks": {mount: disk_percent(mount) for mount in mounts},
    }


def snapshot(mounts=("/",), record=True):
    body = evaluate(read_host(mounts))
    body["taken_at"] = datetime.now(timezone.utc).isoformat()
    if record:
        HISTORY.append({"taken_at": body["taken_at"], "status": body["status"], "load_percent": body["load_percent"]})
    return body


def prometheus(body):
    lines = [
        "# TYPE host_cpu_count gauge",
        f"host_cpu_count {body['cpu_count']}",
        "# TYPE host_disk_used_percent gauge",
    ]
    for mount, percent in body["disks"].items():
        lines.append(f'host_disk_used_percent{{mount="{mount}"}} {percent}')
    if body["load_1m"] is not None:
        lines += ["# TYPE host_load_1m gauge", f"host_load_1m {body['load_1m']}"]
    if body["memory_used_percent"] is not None:
        lines += ["# TYPE host_memory_used_percent gauge", f"host_memory_used_percent {body['memory_used_percent']}"]
    lines += ["# TYPE host_status_critical gauge", f"host_status_critical {1 if body['status'] == 'critical' else 0}"]
    return "\n".join(lines) + "\n"
