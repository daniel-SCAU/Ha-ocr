"""HTTP server for the standalone OCR application."""
from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .ocr_core import capture_and_analyze

_LOGGER = logging.getLogger(__name__)


class OcrRequestHandler(BaseHTTPRequestHandler):
    """Serve OCR endpoints."""

    server_version = "ha-ocr-standalone/1.0"

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/ocr":
            self._send_json(404, {"error": "not found"})
            return

        try:
            body = self._parse_json_body()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON payload"})
            return

        device = body.get("device", "/dev/video0")
        roi_raw = body.get("roi", [0, 0, 0, 0])
        expected_texts_raw = body.get("expected_texts", [])
        ocr_lang = body.get("ocr_lang", "eng")

        if not isinstance(device, str) or not isinstance(ocr_lang, str):
            self._send_json(400, {"error": "device and ocr_lang must be strings"})
            return

        if (
            not isinstance(roi_raw, list)
            or len(roi_raw) != 4
            or not all(isinstance(v, int) for v in roi_raw)
        ):
            self._send_json(400, {"error": "roi must be a list of 4 integers"})
            return

        if not isinstance(expected_texts_raw, list) or not all(
            isinstance(v, str) for v in expected_texts_raw
        ):
            self._send_json(400, {"error": "expected_texts must be a list of strings"})
            return

        try:
            result = capture_and_analyze(
                device=device,
                roi=tuple(roi_raw),
                expected_texts=expected_texts_raw,
                ocr_lang=ocr_lang,
            )
        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("OCR processing failed")
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(200, result)


def main() -> None:
    """Run the standalone OCR server."""
    logging.basicConfig(
        level=os.getenv("OCR_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    host = os.getenv("OCR_APP_HOST", "0.0.0.0")
    port = int(os.getenv("OCR_APP_PORT", "8080"))

    with ThreadingHTTPServer((host, port), OcrRequestHandler) as server:
        _LOGGER.info("Starting OCR server on %s:%s", host, port)
        server.serve_forever()


if __name__ == "__main__":
    main()
