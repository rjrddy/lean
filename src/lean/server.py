"""Live policy lab plus labelled, retained model evaluation. No user code execution."""

from __future__ import annotations

import hmac
import json
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from lean.policy import POLICIES, ROOT, Middleware, Tool
from lean.tasks import tasks

DATA_ROOT = Path(os.getenv("LEAN_ROOT", str(ROOT)))


class Server(ThreadingHTTPServer):
    daemon_threads = True
    token: str = ""


class Handler(BaseHTTPRequestHandler):
    server: Server

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, fmt: str, *args) -> None:
        pass

    def send(self, code: int, data: bytes, mime: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; "
            "style-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(data)

    def dispatch(self, post: bool) -> None:
        status = 500
        try:
            path = urlsplit(self.path).path
            if path.startswith("/api/"):
                if (
                    path != "/api/health"
                    and self.server.token
                    and not hmac.compare_digest(
                        self.headers.get("Authorization", ""), "Bearer " + self.server.token
                    )
                ):
                    status = 401
                    self.send(status, b'{"error":"authentication required"}')
                    return
                origin = self.headers.get("Origin")
                if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                    status = 403
                    self.send(status, b'{"error":"origin rejected"}')
                    return
                if not post and path == "/api/health":
                    result = {"status": "ready"}
                elif not post and path == "/api/report":
                    result = json.loads((DATA_ROOT / "docs/results/evaluation.json").read_text())
                elif not post and path == "/api/policies":
                    result = {"policies": [asdict(p) for p in POLICIES], "tasks": tasks()}
                elif post and path == "/api/lab":
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 65536:
                        status = 413
                        self.send(status, b'{"error":"body limit"}')
                        return
                    body = json.loads(self.rfile.read(length))
                    policy = next(p for p in POLICIES if p.name == body["policy"])
                    fixture = next(t for t in tasks() if t["id"] == body["task"])
                    text = body.get("text", fixture["context"])
                    middleware = Middleware(policy, "live-synthetic-request")
                    tool = Tool("test.report", "fixture-v1", True)
                    first = middleware.call(tool, {"task": fixture["id"]}, lambda _: text)
                    second = middleware.call(tool, {"task": fixture["id"]}, lambda _: text)
                    result = {
                        "first": first,
                        "second": second,
                        "invocations": middleware.tool_invocations,
                        "cache_hits": middleware.cache_hits,
                        "inference_run": False,
                        "basis": "live compression/cache only; no model executed by this endpoint",
                    }
                else:
                    raise KeyError()
                status = 200
                self.send(status, json.dumps(result, ensure_ascii=False, allow_nan=False).encode())
            else:
                if post:
                    raise KeyError()
                web = (DATA_ROOT / "apps/web/dist").resolve()
                file = (web / path.lstrip("/")).resolve()
                if not file.is_relative_to(web):
                    raise KeyError()
                if not file.is_file():
                    file = web / "index.html"
                mime = {
                    ".html": "text/html; charset=utf-8",
                    ".js": "text/javascript",
                    ".css": "text/css",
                }.get(file.suffix)
                if mime is None:
                    raise KeyError()
                status = 200
                self.send(status, file.read_bytes(), mime)
        except (ValueError, TypeError, StopIteration, RecursionError):
            status = 400
            self.send(status, b'{"error":"invalid request"}')
        except (KeyError, FileNotFoundError):
            status = 404
            self.send(status, b'{"error":"not found"}')
        except Exception:
            self.send(500, b'{"error":"internal error"}')
        finally:
            print(
                json.dumps(
                    {"event": "http", "status": status, "operation": "write" if post else "read"}
                ),
                flush=True,
            )

    def do_GET(self) -> None:
        self.dispatch(False)

    def do_POST(self) -> None:
        self.dispatch(True)


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    token = os.getenv("LEAN_TOKEN", "")
    if host not in ("127.0.0.1", "localhost") and len(token) < 24:
        raise ValueError("non-loopback binding requires a long LEAN_TOKEN")
    server = Server((host, int(os.getenv("PORT", "8092"))), Handler)
    server.token = token
    print(json.dumps({"event": "ready", "url": f"http://{host}:{server.server_port}"}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
