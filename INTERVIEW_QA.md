# system-health-dashboard — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does system-health-dashboard address, and what can you demonstrate?

A small API reads the machine it is running on and grades load, memory, and each disk as `ok`, `warn`, or `critical`.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/healthdash/main.py`](src/healthdash/main.py): Implementation or supporting configuration.
- [`src/healthdash/host.py`](src/healthdash/host.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`tests/test_host.py`](tests/test_host.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `evaluate` and explain the decision it makes?

The main walkthrough here is `evaluate(readings, warn=WARN_PERCENT, critical=CRITICAL_PERCENT)` in [`src/healthdash/host.py`](src/healthdash/host.py#L49).

```python
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
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `checks.items`, `checks.values`, `level`, `max`, `readings['disks'].items`, `round`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `parse_meminfo` have?

`parse_meminfo(text)` is defined in [`src/healthdash/host.py`](src/healthdash/host.py#L11).

Its return expressions include:

- `round((total - available) / total * 100, 1)`
- `None`

It uses `int`, `line.split`, `parts[0].isdigit`, `raw.strip`, `raw.strip().split`, `round`, `text.splitlines`, `values.get`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(status_code=422, detail=f"not a directory: {', '.join(missing)}")` in [`src/healthdash/main.py`](src/healthdash/main.py#L15).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_host.py`](tests/test_host.py#L20) contains `test_meminfo_uses_available_not_free`:

```python
def test_meminfo_uses_available_not_free():
    assert parse_meminfo(MEMINFO) == 75.0
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/healthdash/main.py`](src/healthdash/main.py#L20).
- `GET /host` → `host` in [`src/healthdash/main.py`](src/healthdash/main.py#L25).
- `GET /host/history` → `history` in [`src/healthdash/main.py`](src/healthdash/main.py#L30).
- `GET /metrics` → `metrics` in [`src/healthdash/main.py`](src/healthdash/main.py#L36).
- `GET /` → `dashboard` in [`src/healthdash/main.py`](src/healthdash/main.py#L41).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. How would you investigate data ownership and persistence?

Trace the data/configuration files and the code that reads or writes them in the component table. Identify which files are examples, which records are mutable, and which external store is actually configured. I would document those facts before discussing retention, backup, or tenant isolation.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `evaluate`?

In [`src/healthdash/host.py`](src/healthdash/host.py#L49), `evaluate(readings, warn=WARN_PERCENT, critical=CRITICAL_PERCENT)` receives the inputs. The function computes these intermediate values:

- `cpu_count = max(1, readings['cpu_count'])`
- `load = readings['load_1m']`
- `load_percent = None if load is None else round(load / cpu_count * 100, 1)`
- `checks = {'load': level(load_percent, warn, critical), 'memory': level(readings['memory_used_percent'], warn, critical)}`
- `alerts = [f'{name} is {state}' for name, state in checks.items() if state in {'warn', 'critical'}]`

Its result is defined by:

- `{**readings, 'load_percent': load_percent, 'checks': checks, 'status': status, 'alerts': alerts, 'thresholds': {'warn': warn, 'critical': critical}}`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/healthdash/host.py`](src/healthdash/host.py#L49) branches on:

- `'critical' in checks.values()`
- `'warn' in checks.values()`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.
