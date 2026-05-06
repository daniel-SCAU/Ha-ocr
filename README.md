# Ha OCR — Home Assistant USB Camera OCR Integration

A Home Assistant custom integration that captures images from a USB camera,
crops a configurable Region of Interest (ROI) with OpenCV, extracts text using
Tesseract OCR, and compares the result against user-defined text patterns.

---

## Features

| Feature | Detail |
|---|---|
| **Camera capture** | Reads a single frame from `/dev/video0` (or any V4L2 device) via OpenCV |
| **ROI cropping** | Configurable `(x, y, width, height)` rectangle; set width/height to `0` for full-frame |
| **OCR** | Tesseract via `pytesseract`; configurable language code (default `eng`) |
| **Text comparison** | Case-insensitive substring match against a comma-separated list of expected strings |
| **Trigger-based** | No background polling — capture is triggered by pressing the **Capture** button entity or calling the `ha_ocr.capture` service |
| **Options flow** | Device path, ROI, and expected texts can be updated at any time without re-adding the integration |

---

## Requirements

### System packages

```bash
# Tesseract OCR engine (required by pytesseract)
sudo apt install tesseract-ocr

# Optional: extra language packs, e.g. German
sudo apt install tesseract-ocr-deu
```

### Python packages (installed automatically by Home Assistant)

- `opencv-python-headless >= 4.5.0, != 4.10.0.84, != 4.11.0.86`
- `pytesseract >= 0.3.10`
- `Pillow >= 9.0.0`

---

## Installation

1. Copy the `custom_components/ha_ocr` folder into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and search for
   **Ha OCR**.

---

## Standalone OCR Docker container

A separate OCR application container is available in `docker/ocr/` and does
not require Home Assistant.

### Build

```bash
docker build -t ha-ocr-app -f docker/ocr/Dockerfile .
```

### Run

```bash
docker run --rm -p 8080:8080 --device /dev/video0:/dev/video0 ha-ocr-app
```

By default the server binds to `0.0.0.0` inside the container. For restricted
exposure, set `OCR_APP_HOST=127.0.0.1` and publish only to trusted interfaces.

### API

- `GET /health` → health check
- `POST /ocr` → capture + OCR + text comparison

Example:

```bash
curl -X POST http://localhost:8080/ocr \
  -H "Content-Type: application/json" \
  -d '{
    "device": "/dev/video0",
    "roi": [0, 0, 0, 0],
    "expected_texts": ["meter", "kwh"],
    "ocr_lang": "eng"
  }'
```

---

## Configuration

| Field | Default | Description |
|---|---|---|
| Camera device path | `/dev/video0` | V4L2 device node |
| ROI X offset | `0` | Left edge of the crop region (pixels) |
| ROI Y offset | `0` | Top edge of the crop region (pixels) |
| ROI width | `0` | Width of crop region (`0` = full frame) |
| ROI height | `0` | Height of crop region (`0` = full frame) |
| Expected texts | *(empty)* | Comma-separated patterns to match (case-insensitive) |
| OCR language | `eng` | Tesseract language code |

---

## Entities

| Entity | Type | Description |
|---|---|---|
| `sensor.<name>_ocr_text` | Sensor | Raw text extracted by Tesseract |
| `sensor.<name>_ocr_match` | Sensor | `match` or `no_match` |
| `button.<name>_capture` | Button | Press to trigger a new capture |

### Extra state attributes

**OCR Text sensor**

| Attribute | Type | Description |
|---|---|---|
| `match` | `bool` | Whether any expected text was found |
| `matched_texts` | `list[str]` | All expected patterns that matched |

**OCR Match sensor**

| Attribute | Type | Description |
|---|---|---|
| `ocr_text` | `str` | Raw OCR result |
| `matched_texts` | `list[str]` | All expected patterns that matched |

---

## Service: `ha_ocr.capture`

Trigger a capture programmatically (e.g. from an automation).

```yaml
service: ha_ocr.capture
data:
  entry_id: "<config_entry_id>"   # optional — omit to trigger ALL entries
```

---

## Example automation

```yaml
automation:
  - alias: "OCR on motion"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      - service: ha_ocr.capture
```

---

## Development & Testing

```bash
pip install -r requirements_test.txt
pytest tests/ -v
```

All tests mock OpenCV and pytesseract so no camera or Tesseract installation is
needed to run them.

---

## Project structure

```
custom_components/ha_ocr/
├── __init__.py          # async_setup_entry / async_unload_entry + service registration
├── manifest.json        # Integration metadata & pip requirements
├── config_flow.py       # UI config flow + options flow
├── const.py             # Domain constants
├── coordinator.py       # DataUpdateCoordinator (trigger-based, no auto-poll)
├── ocr.py               # Camera capture, ROI crop, Tesseract OCR, text comparison
├── sensor.py            # OcrTextSensor + OcrMatchSensor
├── button.py            # OcrCaptureButton
├── services.yaml        # Service schema
├── strings.json         # UI strings (source)
└── translations/
    └── en.json          # English translations
```
