from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from healthdash.host import snapshot

app = FastAPI(title="System health")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/host")
def host():
    return snapshot()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    body = snapshot()
    items = "".join(f"<li>{item}</li>" for item in body["alerts"]) or "<li>none</li>"
    return f"<h1>Host</h1><p>Load {body['load_1m']}</p><p>Disk {body['disk_used_percent']}%</p><ul>{items}</ul>"
