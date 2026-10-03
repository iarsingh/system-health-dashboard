# System health dashboard

Level: Beginner

Skills: Python, FastAPI, Linux, REST

A small API reads the machine it is running on and returns load, disk, and memory.

On Linux, memory comes from `/proc/meminfo`. On a Mac that file is absent, so memory is null and disk plus load still return.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn healthdash.main:app --reload
```

`GET /host` is the JSON. `GET /` is the same numbers as a page. This does not SSH to other machines and it does not open a firewall rule.

