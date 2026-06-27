from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .external_apis import ExternalApiError
from .models import CampaignConfig
from .pipeline import LeadGenerationPipeline
from .storage import LeadRepository

DB_PATH = "data/leadgen.db"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def to_jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


class LeadGenHandler(BaseHTTPRequestHandler):
    repository = LeadRepository(DB_PATH)
    pipeline = LeadGenerationPipeline(repository)

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(to_jsonable(payload), indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/":
                body = (STATIC_DIR / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/leads":
                self._send_json({"leads": self.repository.list_leads()})
            elif path == "/api/health":
                self._send_json({"ok": True})
            else:
                self._send_json({"error": "Not found"}, 404)
        except OSError as exc:
            self._send_json({"error": "Unable to read requested resource", "detail": str(exc)}, 500)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path != "/api/campaigns/run":
                self._send_json({"error": "Not found"}, 404)
                return
            data = self._read_json()
            config = CampaignConfig(
                niche=str(data.get("niche", "")).strip(),
                location=str(data.get("location", "")).strip(),
                budget=float(data.get("budget", 0)),
                min_quality=int(data.get("min_quality", 60)),
                limit=int(data.get("limit", 10)),
            )
            leads = self.pipeline.run(config)
            self._send_json({"campaign": asdict(config), "saved_count": len(leads), "leads": leads}, 201)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
        except ExternalApiError as exc:
            self._send_json({"error": "External provider failed", "detail": str(exc)}, 502)
        except Exception as exc:  # Last-resort API safety boundary.
            self._send_json({"error": "Unexpected server error", "detail": str(exc)}, 500)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), LeadGenHandler)
    print("Lead generation admin running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
