#!/usr/bin/env python3
"""Localhost-only control-file API for the ARRP Run Coordinator Bot."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from arrp_context import contained_path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / ".tmp" / "run-coordinator" / "control.json"
DEFAULT_MANIFEST = ROOT / ".tmp" / "run-chain.json"
DEFAULT_TOKEN_FILE = ROOT / ".tmp" / "run-coordinator" / "control.token"
ALLOWED_ORIGIN_HEADERS = {
    "http://127.0.0.1:8765": "http://127.0.0.1:8765",
    "http://localhost:8765": "http://localhost:8765",
}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,159}$")
ACTIONS = {
    "request_run",
    "request_comprehensive_review",
    "reprioritize",
    "suppress",
    "clear_override",
}
PRIORITIES = {"critical", "high", "normal", "low"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any, root: Path = ROOT) -> Any:
    safe_path = contained_path(path, root)
    if not safe_path.is_file():
        return default
    return json.loads(safe_path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], root: Path = ROOT) -> None:
    safe_path = contained_path(path, root)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = safe_path.with_suffix(safe_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(safe_path)


def load_or_create_token(path: Path, root: Path = ROOT) -> str:
    safe_path = contained_path(path, root)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    if safe_path.is_file():
        token = safe_path.read_text(encoding="utf-8").strip()
        if len(token) < 32:
            raise ValueError("stored coordinator control token is invalid")
        safe_path.chmod(0o600)
        return token
    token = secrets.token_urlsafe(32)
    descriptor = os.open(
        safe_path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(token + "\n")
    return token


def valid_work_unit(value: Any) -> bool:
    return (
        isinstance(value, str)
        and ID_PATTERN.fullmatch(value) is not None
        and ".." not in value
        and not value.startswith("/")
    )


def apply_control(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    if action not in ACTIONS:
        raise ValueError("unsupported control action")
    reason = str(payload.get("reason") or "").strip()
    if len(reason) > 500:
        raise ValueError("reason exceeds 500 characters")
    work_unit = payload.get("work_unit_id")
    if action in {"reprioritize", "suppress", "clear_override"} and not valid_work_unit(
        work_unit
    ):
        raise ValueError("a valid work_unit_id is required")
    if action == "reprioritize" and payload.get("priority") not in PRIORITIES:
        raise ValueError("priority must be critical, high, normal, or low")
    state.setdefault("schema_version", 1)
    state.setdefault("overrides", {})
    state.setdefault("requests", [])
    request_id = "control-" + secrets.token_hex(8)
    record = {
        "request_id": request_id,
        "action": action,
        "work_unit_id": work_unit,
        "created_at": now(),
        "source": "user-local-console",
        "reason": reason,
    }
    if action == "request_run":
        state["requested_run"] = record
    elif action == "request_comprehensive_review":
        record["full_context"] = bool(payload.get("full_context", True))
        state["requested_comprehensive_review"] = record
    elif action == "reprioritize":
        record["priority"] = payload["priority"]
        state["overrides"][work_unit] = record
    elif action == "suppress":
        record["suppressed"] = True
        state["overrides"][work_unit] = record
    elif action == "clear_override":
        existing = state["overrides"].get(work_unit)
        if not existing or existing.get("source") != "user-local-console":
            raise ValueError("no user-created override exists for this work unit")
        record["cleared_request_id"] = existing.get("request_id")
        del state["overrides"][work_unit]
    state["requests"].append(record)
    state["requests"] = state["requests"][-100:]
    state["updated_at"] = now()
    return record


def handler(
    state_path: Path, manifest_path: Path, token: str
) -> type[BaseHTTPRequestHandler]:
    class ControlHandler(BaseHTTPRequestHandler):
        server_version = "ARRPRunCoordinatorControl/1"

        def cors(self) -> None:
            safe_origin = ALLOWED_ORIGIN_HEADERS.get(self.headers.get("Origin", ""))
            if safe_origin:
                self.send_header("Access-Control-Allow-Origin", safe_origin)
                self.send_header("Vary", "Origin")

        def response(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.cors()
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            if self.headers.get("Origin", "") not in ALLOWED_ORIGIN_HEADERS:
                self.response(403, {"error": "origin not allowed"})
                return
            self.send_response(204)
            self.cors()
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, X-ARRP-Control-Token",
            )
            self.end_headers()

        def do_GET(self) -> None:
            if self.path != "/v1/status":
                self.response(404, {"error": "not found"})
                return
            if self.headers.get("Origin", "") not in ALLOWED_ORIGIN_HEADERS:
                self.response(403, {"error": "origin not allowed"})
                return
            self.response(
                200,
                {
                    "available": True,
                    "control_token": token,
                    "control": read_json(state_path, {"schema_version": 1}),
                    "manifest": read_json(manifest_path, None),
                },
            )

        def do_POST(self) -> None:
            if self.path != "/v1/control":
                self.response(404, {"error": "not found"})
                return
            if self.headers.get("Origin", "") not in ALLOWED_ORIGIN_HEADERS:
                self.response(403, {"error": "origin not allowed"})
                return
            if self.headers.get("X-ARRP-Control-Token") != token:
                self.response(403, {"error": "invalid control token"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 4096:
                    raise ValueError("control request must be 1 through 4096 bytes")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("control request must be a JSON object")
                state = read_json(
                    state_path,
                    {"schema_version": 1, "overrides": {}, "requests": []},
                )
                record = apply_control(state, payload)
                write_json(state_path, state)
            except (json.JSONDecodeError, OSError, ValueError) as exc:
                self.response(400, {"error": str(exc)})
                return
            self.response(200, {"ok": True, "record": record})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ControlHandler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("control service may bind only to localhost")
    token = load_or_create_token(DEFAULT_TOKEN_FILE)
    print("ARRP coordinator control service ready.", flush=True)
    server = ThreadingHTTPServer(
        (args.host, args.port), handler(DEFAULT_STATE, DEFAULT_MANIFEST, token)
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
