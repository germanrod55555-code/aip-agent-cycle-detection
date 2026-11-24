"""Локальный интерфейс, доступный только с этого компьютера."""

import json
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .algorithms import ALGORITHMS
from .models import Trajectory, ReportAgent
from .agent import run_agent


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        try:
            if request.path == "/":
                data = Path(__file__).with_name("interface.html").read_bytes()
                kind = "text/html; charset=utf-8"
            elif request.path == "/api/compare":
                args = parse_qs(request.query)
                mu = int(args.get("mu", [3])[0])
                lam = int(args.get("lam", [4])[0])
                length = int(args["length"][0]) if "length" in args else None
                if not 0 <= mu <= 100000 or not 1 <= lam <= 100000:
                    raise ValueError("Допустимо: 0 ≤ μ ≤ 100000, 1 ≤ λ ≤ 100000")
                if length is not None and not 0 <= length <= 100000:
                    raise ValueError("Длина цепочки: от 0 до 100000")
                model = Trajectory(mu, lam, length)
                result = {name: asdict(fn(model.start, model, 2_000_000))
                          for name, fn in ALGORITHMS.items()}
                data = json.dumps(result, ensure_ascii=False).encode("utf-8")
                kind = "application/json; charset=utf-8"
            elif request.path == "/api/agent":
                args = parse_qs(request.query)
                result = run_agent(ReportAgent(args.get("scenario", ["loop"])[0]))
                data = json.dumps(result, ensure_ascii=False).encode("utf-8")
                kind = "application/json; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
        except (ValueError, TypeError) as exc:
            data = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            kind = "application/json; charset=utf-8"
            self.send_response(400)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass


def serve(port=8766, open_browser=True):
    address = f"http://127.0.0.1:{port}/"
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Демонстрация: {address}\nДля остановки нажмите Ctrl+C.", flush=True)
    if open_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
