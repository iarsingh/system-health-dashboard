import os
import shutil


def memory_percent():
    meminfo = "/proc/meminfo"
    if not os.path.exists(meminfo):
        return None
    values = {}
    for line in open(meminfo, encoding="utf-8"):
        key, raw = line.split(":", 1)
        values[key] = int(raw.strip().split()[0])
    total = values.get("MemTotal") or 0
    available = values.get("MemAvailable") or 0
    if total <= 0:
        return None
    return round((total - available) / total * 100, 1)


def snapshot():
    disk = shutil.disk_usage("/")
    load = os.getloadavg()[0]
    memory = memory_percent()
    alerts = []
    disk_percent = round(disk.used / disk.total * 100, 1)
    if disk_percent >= 90:
        alerts.append("disk above 90 percent")
    if load >= max(1, os.cpu_count() or 1):
        alerts.append("load at or above CPU count")
    if memory is not None and memory >= 90:
        alerts.append("memory above 90 percent")
    return {
        "load_1m": load,
        "cpu_count": os.cpu_count() or 1,
        "disk_used_percent": disk_percent,
        "memory_used_percent": memory,
        "alerts": alerts,
    }
