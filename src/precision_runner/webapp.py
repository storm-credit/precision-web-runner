from __future__ import annotations

import argparse
import json
import signal
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .service import RunnerService


class ApiHandler(BaseHTTPRequestHandler):
    service: RunnerService
    static_dir = Path(__file__).with_name("static")

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[http] {self.address_string()} - {fmt % args}")

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        if self.path == "/api/status":
            self._json(HTTPStatus.OK, {"ok": True, "data": self.service.status()})
            return
        if self.path in ("/", "/index.html"):
            data = (self.static_dir / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        routes = {
            "/api/task": self._save_task,
            "/api/browser/open": self._open_browser,
            "/api/preflight": self._preflight,
            "/api/arm": self._arm,
            "/api/cancel": self._cancel,
            "/api/run-now": self._run_now,
            "/api/continue": self._continue,
        }
        fn = routes.get(self.path)
        if fn is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            result = fn()
        except (ValueError, RuntimeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
        else:
            self._json(HTTPStatus.OK, {"ok": True, "data": result})

    def _save_task(self) -> dict[str, Any]:
        return self.service.save_task(self._body())

    def _open_browser(self) -> dict[str, Any]:
        return self.service.open_browser()

    def _preflight(self) -> dict[str, Any]:
        return self.service.preflight()

    def _arm(self) -> dict[str, Any]:
        return self.service.arm()

    def _cancel(self) -> dict[str, Any]:
        return self.service.cancel()

    def _run_now(self) -> dict[str, Any]:
        body = self._body()
        if body.get("confirmation") != "RUN_CHECKOUT_NOW":
            raise ValueError("explicit RUN_CHECKOUT_NOW confirmation is required")
        return self.service.run_now()

    def _continue(self) -> dict[str, Any]:
        body = self._body()
        return self.service.continue_manual(open_payment=bool(body.get("openPayment", False)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Precision Web Runner POC")
    parser.add_argument("--host", default="127.0.0.1", help="POC defaults to localhost only")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="do not open dashboard automatically")
    args = parser.parse_args()

    if args.host not in ("127.0.0.1", "localhost"):
        print("WARNING: POC dashboard has no authentication. Do not expose it to untrusted networks.")

    service = RunnerService()
    ApiHandler.service = service
    server = ThreadingHTTPServer((args.host, args.port), ApiHandler)

    def shutdown(*_: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, shutdown)
    try:
        signal.signal(signal.SIGTERM, shutdown)
    except AttributeError:
        pass

    url = f"http://{args.host}:{args.port}/"
    print(f"Precision Runner: {url}")
    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        service.close()
        server.server_close()


if __name__ == "__main__":
    main()
