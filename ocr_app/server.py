"""HTTP server for the standalone OCR application."""
from __future__ import annotations

import base64
import binascii
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .ocr_core import analyze_frame, capture_and_analyze

_LOGGER = logging.getLogger(__name__)
_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HA OCR Local Tester</title>
  <style>
    body { font-family: sans-serif; margin: 24px; max-width: 920px; }
    .row { display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 12px; }
    label { display: block; font-size: 14px; margin-bottom: 8px; }
    input, select, textarea, button { width: 100%; padding: 8px; box-sizing: border-box; }
    textarea { min-height: 72px; }
    .muted { color: #666; font-size: 12px; }
    pre { background: #f5f5f5; padding: 12px; overflow: auto; }
  </style>
</head>
<body>
  <h1>HA OCR Local Tester</h1>
  <p class="muted">Use camera device or upload an image to test ROI/expected-text configuration locally.</p>

  <div class="row">
    <label>Input mode
      <select id="input_mode">
        <option value="camera">Camera device</option>
        <option value="upload">Uploaded image</option>
      </select>
    </label>
    <label>Camera device
      <input id="device" value="/dev/video0">
    </label>
  </div>

  <div class="row">
    <label>ROI X<input id="roi_x" type="number" value="0"></label>
    <label>ROI Y<input id="roi_y" type="number" value="0"></label>
    <label>ROI Width<input id="roi_w" type="number" value="0"></label>
    <label>ROI Height<input id="roi_h" type="number" value="0"></label>
  </div>

  <div class="row">
    <label>OCR language
      <input id="ocr_lang" value="eng">
    </label>
    <label>Image file (for upload mode)
      <input id="image_file" type="file" accept="image/*">
    </label>
  </div>

  <label>Expected texts (comma-separated)
    <textarea id="expected_texts" placeholder="Actief Hartmanns, VPN activated"></textarea>
  </label>

  <button id="run_btn">Run OCR test</button>
  <p class="muted" id="status"></p>
  <pre id="result">{}</pre>

  <script>
    async function fileToDataUrl(file) {
      return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    document.getElementById("run_btn").addEventListener("click", async () => {
      const mode = document.getElementById("input_mode").value;
      const file = document.getElementById("image_file").files[0];
      const expectedTexts = document.getElementById("expected_texts").value
        .split(",")
        .map((v) => v.trim())
        .filter((v) => v.length > 0);

      const payload = {
        device: document.getElementById("device").value,
        roi: [
          Number.parseInt(document.getElementById("roi_x").value || "0", 10),
          Number.parseInt(document.getElementById("roi_y").value || "0", 10),
          Number.parseInt(document.getElementById("roi_w").value || "0", 10),
          Number.parseInt(document.getElementById("roi_h").value || "0", 10),
        ],
        expected_texts: expectedTexts,
        ocr_lang: document.getElementById("ocr_lang").value || "eng",
      };

      if (mode === "upload") {
        if (!file) {
          document.getElementById("status").textContent = "Select an image file for upload mode.";
          return;
        }
        payload.image_base64 = await fileToDataUrl(file);
      }

      document.getElementById("status").textContent = "Running...";
      const res = await fetch("/ocr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      document.getElementById("result").textContent = JSON.stringify(json, null, 2);
      document.getElementById("status").textContent = "HTTP " + res.status;
    });
  </script>
</body>
</html>
"""


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

    def _send_html(self, status_code: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _parse_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def _decode_image_base64(image_base64: str):
        import cv2  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415

        payload = image_base64.strip()
        if payload.startswith("data:"):
            _, _, payload = payload.partition(",")
        try:
            image_bytes = base64.b64decode(payload, validate=True)
        except binascii.Error as exc:
            raise ValueError("image_base64 is not valid base64") from exc
        data = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Uploaded image could not be decoded")
        return frame

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(200, _INDEX_HTML)
            return
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
        image_base64 = body.get("image_base64")

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

        if image_base64 is not None and not isinstance(image_base64, str):
            self._send_json(400, {"error": "image_base64 must be a string when provided"})
            return

        try:
            if image_base64:
                frame = self._decode_image_base64(image_base64)
                result = analyze_frame(
                    frame=frame,
                    roi=tuple(roi_raw),
                    expected_texts=expected_texts_raw,
                    ocr_lang=ocr_lang,
                )
            else:
                result = capture_and_analyze(
                    device=device,
                    roi=tuple(roi_raw),
                    expected_texts=expected_texts_raw,
                    ocr_lang=ocr_lang,
                )
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except OSError as exc:
            _LOGGER.warning("OCR runtime environment error: %s", exc)
            self._send_json(
                500,
                {"error": f"ocr runtime environment error: {exc}"},
            )
            return
        except RuntimeError as exc:
            _LOGGER.warning("OCR request failed: %s", exc)
            self._send_json(400, {"error": str(exc)})
            return
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected OCR processing failure")
            self._send_json(
                500,
                {"error": "internal OCR processing error; check server logs for details"},
            )
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
