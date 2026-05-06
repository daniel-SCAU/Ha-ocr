"""Core OCR capture and processing logic for the standalone OCR app."""
from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def capture_image(device: str) -> Any:
    """Capture a single frame from a camera device using OpenCV."""
    import cv2  # noqa: PLC0415

    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera device: {device}")
    try:
        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError(f"Failed to capture frame from {device}")
        return frame
    finally:
        cap.release()


def crop_roi(frame: Any, roi: tuple[int, int, int, int]) -> Any:
    """Crop a region of interest from an image frame."""
    x, y, w, h = roi
    if w > 0 and h > 0:
        frame_h, frame_w = frame.shape[:2]
        x1 = max(0, min(x, frame_w))
        y1 = max(0, min(y, frame_h))
        x2 = max(0, min(x + w, frame_w))
        y2 = max(0, min(y + h, frame_h))
        return frame[y1:y2, x1:x2]
    return frame


def run_ocr(frame: Any, lang: str = "eng") -> str:
    """Run Tesseract OCR on an OpenCV image frame."""
    import cv2  # noqa: PLC0415
    import pytesseract  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    return pytesseract.image_to_string(pil_image, lang=lang).strip()


def compare_text(ocr_text: str, expected_texts: list[str]) -> dict[str, Any]:
    """Compare OCR text to expected patterns (case-insensitive substring match)."""
    ocr_lower = ocr_text.lower()
    matched = [t for t in expected_texts if t and t.lower() in ocr_lower]
    return {
        "is_match": len(matched) > 0,
        "matched_texts": matched,
    }


def capture_and_analyze(
    device: str,
    roi: tuple[int, int, int, int],
    expected_texts: list[str],
    ocr_lang: str = "eng",
) -> dict[str, Any]:
    """Capture, crop, OCR, and compare text in one operation."""
    _LOGGER.debug("Capturing image from %s with ROI %s", device, roi)
    frame = capture_image(device)
    cropped = crop_roi(frame, roi)
    ocr_text = run_ocr(cropped, lang=ocr_lang)
    _LOGGER.debug("OCR result: %r", ocr_text)
    comparison = compare_text(ocr_text, expected_texts)
    return {
        "ocr_text": ocr_text,
        **comparison,
    }
