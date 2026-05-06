"""OCR capture and processing logic for the Ha OCR integration.

This module provides helper functions for:
  - Capturing a frame from a USB camera via OpenCV (``capture_image``)
  - Cropping a region-of-interest from the frame (``crop_roi``)
  - Running Tesseract OCR on the cropped image (``run_ocr``)
  - Comparing the OCR result against configurable text patterns (``compare_text``)
  - A convenience function that orchestrates the full pipeline (``capture_and_analyze``)

Dependencies (installed via ``manifest.json`` requirements):
  - ``opencv-python-headless``
  - ``pytesseract``  (also requires the ``tesseract-ocr`` system package)
  - ``Pillow``
"""
from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def capture_image(device: str) -> Any:
    """Capture a single frame from a camera device using OpenCV.

    Args:
        device: Camera device path, e.g. ``'/dev/video0'``.

    Returns:
        A BGR numpy array (OpenCV frame).

    Raises:
        RuntimeError: If the device cannot be opened or the frame read fails.
    """
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
    """Crop the region of interest (ROI) from an image frame.

    Args:
        frame: OpenCV BGR numpy array.
        roi: ``(x, y, width, height)``.  When *width* or *height* is ``0``
             the original frame is returned unchanged (full-frame mode).

    Returns:
        Cropped frame, or the original frame when ROI dimensions are zero.
    """
    x, y, w, h = roi
    if w > 0 and h > 0:
        return frame[y : y + h, x : x + w]
    return frame


def run_ocr(frame: Any, lang: str = "eng") -> str:
    """Run Tesseract OCR on an OpenCV image frame.

    Args:
        frame: OpenCV BGR numpy array.
        lang: Tesseract language code (default: ``'eng'``).

    Returns:
        Extracted text stripped of leading/trailing whitespace.
    """
    import cv2  # noqa: PLC0415
    import pytesseract  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    return pytesseract.image_to_string(pil_image, lang=lang).strip()


def compare_text(ocr_text: str, expected_texts: list[str]) -> dict[str, Any]:
    """Compare an OCR result against a list of expected text patterns.

    A match is found when an expected text is a *substring* of the OCR result
    (case-insensitive).

    Args:
        ocr_text: Text extracted by OCR.
        expected_texts: List of text strings to search for.

    Returns:
        Dict with:
          - ``is_match`` (``bool``): ``True`` if at least one pattern was found.
          - ``matched_texts`` (``list[str]``): All patterns that were found.
    """
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
    """Capture an image, crop the ROI, run OCR, and compare against expected texts.

    This is the high-level function called by the coordinator.  It runs in a
    thread-pool executor because all underlying operations are blocking.

    Args:
        device: Camera device path (e.g. ``'/dev/video0'``).
        roi: Region of interest as ``(x, y, width, height)``.
        expected_texts: List of expected text patterns to match against.
        ocr_lang: Tesseract language code.

    Returns:
        Dict with ``ocr_text``, ``is_match``, and ``matched_texts``.
    """
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
