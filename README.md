# System health dashboard

Level: Beginner

Skills: Python, FastAPI, Linux, REST, Prometheus text format

A small API reads the machine it is running on and grades load, memory, and each disk as `ok`, `warn`, or `critical`.

On Linux, memory comes from `MemAvailable` in `/proc/meminfo`, not `MemFree`, because the kernel page cache is reclaimable. On a Mac that file is absent, so memory is `unknown` and it does not raise an alert. Load is judged per CPU: a load of 3.6 on 4 CPUs is 90 percent. If the platform will not report a load average, load is `unknown` instead of an error.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn healthdash.main:app --reload
```

| Endpoint | Returns |
| --- | --- |
| `GET /host` | Readings, a check per resource, overall status, alerts |
| `GET /host?mount=/&mount=/data` | The same, with one check per mount |
| `GET /host/history?limit=20` | The last snapshots taken by `/host` and `/` |
| `GET /metrics` | Prometheus text for a scrape |
| `GET /` | The same numbers as a page |

Thresholds default to warn at 80 and critical at 90. Change them with `HEALTH_WARN_PERCENT` and `HEALTH_CRITICAL_PERCENT`. History keeps 60 snapshots in memory; change that with `HEALTH_HISTORY`.

A mount that is not a directory is refused. This does not SSH to other machines and it does not open a firewall rule.
