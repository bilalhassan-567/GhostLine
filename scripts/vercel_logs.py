"""Fetch Vercel deployment status + build/runtime logs via the REST API.

No Node / Vercel CLI needed. Reads a token from VERCEL_TOKEN (or the repo .env).
Create one at https://vercel.com/account/tokens (Read scope is enough).

    python scripts/vercel_logs.py                 # latest deployment: status + errors + recent runtime logs
    python scripts/vercel_logs.py deployments     # list recent deployments
    python scripts/vercel_logs.py build [dpl_id]  # build events for a deployment (default: latest)
    python scripts/vercel_logs.py runtime [dpl_id] [seconds]  # stream runtime logs (default: latest, 8s)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

API = "https://api.vercel.com"
PROJECT = os.environ.get("VERCEL_PROJECT", "ghostline")


def _load_env_token() -> str | None:
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("VERCEL_TOKEN="):
                return line.split("=", 1)[1].strip() or None
    return None


TOKEN = os.environ.get("VERCEL_TOKEN") or _load_env_token()
TEAM = os.environ.get("VERCEL_TEAM_ID")


def _client() -> httpx.Client:
    if not TOKEN:
        sys.exit("Set VERCEL_TOKEN (env or .env). Create one at vercel.com/account/tokens.")
    params = {"teamId": TEAM} if TEAM else {}
    return httpx.Client(
        base_url=API, headers={"Authorization": f"Bearer {TOKEN}"}, params=params, timeout=30
    )


def list_deployments(c: httpx.Client, limit: int = 8) -> list[dict]:
    r = c.get("/v7/deployments", params={"app": PROJECT, "limit": limit})
    r.raise_for_status()
    return r.json().get("deployments", [])


def print_deployments(c: httpx.Client) -> None:
    for d in list_deployments(c):
        ts = time.strftime("%m-%d %H:%M", time.localtime(d["created"] / 1000))
        print(f"{d['uid']}  {d['readyState']:12}  {ts}  {d.get('url', '')}  {d.get('meta', {}).get('githubCommitSha', '')[:7]}")


def build_events(c: httpx.Client, dpl: str) -> None:
    r = c.get(f"/v3/deployments/{dpl}/events", params={"limit": 1000, "builds": 1})
    r.raise_for_status()
    data = r.json()
    events = data if isinstance(data, list) else data.get("events", [])
    for e in events:
        txt = e.get("text") or e.get("payload", {}).get("text") or json.dumps(e.get("payload", {}))
        print(f"[{e.get('type', '?')}] {txt}")


def runtime_logs(c: httpx.Client, dpl: str, seconds: float = 8.0, project_id: str | None = None) -> None:
    pid = project_id or PROJECT
    url = f"/v1/projects/{pid}/deployments/{dpl}/runtime-logs"
    deadline = time.monotonic() + seconds
    try:
        with c.stream("GET", url) as resp:
            if resp.status_code >= 400:
                print(f"runtime-logs {resp.status_code}: {resp.read().decode()[:400]}")
                return
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    o = json.loads(line)
                    lvl = o.get("level", "info")
                    print(f"{o.get('source', '?'):8} {lvl:7} {o.get('message', '')}")
                except json.JSONDecodeError:
                    print(line)
                if time.monotonic() > deadline:
                    break
    except httpx.ReadTimeout:
        pass


def latest(c: httpx.Client) -> None:
    deps = list_deployments(c, 5)
    if not deps:
        print("No deployments found for project", PROJECT)
        return
    d = deps[0]
    print(f"latest: {d['uid']}  state={d['readyState']}  url={d.get('url')}")
    if d.get("errorMessage"):
        print("errorMessage:", d["errorMessage"])
    if d["readyState"] in ("ERROR", "BUILDING", "QUEUED", "INITIALIZING"):
        print("\n--- build events ---")
        build_events(c, d["uid"])
    print("\n--- runtime logs (recent) ---")
    runtime_logs(c, d["uid"], project_id=d.get("projectId"))


def main() -> None:
    args = sys.argv[1:]
    with _client() as c:
        if not args:
            latest(c)
        elif args[0] == "deployments":
            print_deployments(c)
        elif args[0] == "build":
            dpl = args[1] if len(args) > 1 else list_deployments(c, 1)[0]["uid"]
            build_events(c, dpl)
        elif args[0] == "runtime":
            deps = list_deployments(c, 1)
            dpl = args[1] if len(args) > 1 else deps[0]["uid"]
            secs = float(args[2]) if len(args) > 2 else 8.0
            runtime_logs(c, dpl, secs, deps[0].get("projectId"))
        else:
            sys.exit(__doc__)


if __name__ == "__main__":
    main()
