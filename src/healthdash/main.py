import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from healthdash.host import HISTORY, prometheus, snapshot

app = FastAPI(title="System health")


def checked_mounts(mounts):
    chosen = mounts or ["/"]
    missing = [mount for mount in chosen if not os.path.isdir(mount)]
    if missing:
        raise HTTPException(status_code=422, detail=f"not a directory: {', '.join(missing)}")
    return tuple(chosen)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/host")
def host(mount: list[str] = Query(default=[])):
    return snapshot(checked_mounts(mount))


@app.get("/host/history")
def history(limit: int = Query(default=20, ge=1, le=60)):
    rows = list(HISTORY)[-limit:]
    return {"count": len(rows), "snapshots": rows}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return prometheus(snapshot(record=False))


@app.get("/", response_class=HTMLResponse)
def dashboard():
    body = snapshot()
    checks = "".join(f"<tr><td>{name}</td><td>{state}</td></tr>" for name, state in body["checks"].items())
    return (
        f"<h1>Host is {body['status']}</h1>"
        f"<p>Load {body['load_1m']} on {body['cpu_count']} CPUs ({body['load_percent']} percent)</p>"
        f"<table>{checks}</table>"
    )
