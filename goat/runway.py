"""Tiny Runway API client: submit a task, poll it, download the output, log the spend.

The key is read from the file named by RUNWAY_KEY_FILE (never stored in the repo).
"""
import json
import os
import pathlib
import threading
import time
import urllib.error
import urllib.request

API = "https://api.dev.runwayml.com"
HEADERS = {"X-Runway-Version": "2024-11-06", "Content-Type": "application/json"}
LEDGER = pathlib.Path(__file__).parent / "media" / "ledger.jsonl"
_lock = threading.Lock()


def _key():
    return pathlib.Path(os.environ["RUNWAY_KEY_FILE"]).read_text().strip()


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={**HEADERS, "Authorization": f"Bearer {_key()}"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                time.sleep(5 * 2 ** attempt)
                continue
            raise RuntimeError(f"{method} {path} -> {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError):
            time.sleep(3 * 2 ** attempt)
    raise RuntimeError(f"{method} {path} failed after retries")


def credits():
    return _req("GET", "/v1/organization")["creditBalance"]


def run(endpoint, body, out_path, name=None):
    """Submit body to /v1/<endpoint>, wait for it, save output[0] to out_path."""
    out_path = pathlib.Path(out_path)
    if out_path.exists():
        return out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    task = _req("POST", f"/v1/{endpoint}", body)
    tid = task["id"]
    delay = 5
    while True:
        time.sleep(delay)
        t = _req("GET", f"/v1/tasks/{tid}")
        if t["status"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        delay = min(delay + 2, 15)
    with _lock, LEDGER.open("a") as f:
        f.write(json.dumps({"name": name or out_path.name, "model": body.get("model"),
                            "status": t["status"], "cost": t.get("cost"), "id": tid,
                            "failure": t.get("failure"), "output": t.get("output")}) + "\n")
    if t["status"] != "SUCCEEDED":
        raise RuntimeError(f"{name}: {t['status']} {t.get('failureCode')} {t.get('failure')}")
    url = t["output"][0]
    urllib.request.urlretrieve(url, out_path)
    out_path.with_suffix(out_path.suffix + ".url").write_text(url)
    return out_path


def url_of(path):
    """Runway output URL saved next to a downloaded file (valid ~24h) for chaining."""
    return pathlib.Path(str(path) + ".url").read_text().strip()
