"""Unit tests for the OCR processing module (ocr.py).

These tests mock all external I/O (OpenCV, pytesseract, PIL) so the test suite
can run without a physical camera or Tesseract installed.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Lazy-import the module under test so we avoid importing cv2/pytesseract at
# module load time (they may not be installed in the CI test environment).
from custom_components.ha_ocr.ocr import (
    capture_and_analyze,
    capture_image,
    compare_text,
    crop_roi,
    run_ocr,
)


# ---------------------------------------------------------------------------
# capture_image
# ---------------------------------------------------------------------------


class TestCaptureImage:
    """Tests for :func:`capture_image`."""

    def test_capture_success(self):
        """A frame is returned when the camera opens and read succeeds."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            result = capture_image("/dev/video0")

        assert result is mock_frame
        mock_cap.release.assert_called_once()

    def test_capture_device_not_open(self):
        """RuntimeError is raised when the device cannot be opened."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False

        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pytest.raises(RuntimeError, match="Cannot open camera device"):
                capture_image("/dev/video0")

    def test_capture_read_fails(self):
        """RuntimeError is raised when ``cap.read()`` returns ``False``."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pytest.raises(RuntimeError, match="Failed to capture frame"):
                capture_image("/dev/video0")

    def test_capture_releases_on_read_error(self):
        """``cap.release()`` is always called, even when ``read`` fails."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pytest.raises(RuntimeError):
                capture_image("/dev/video0")

        mock_cap.release.assert_called_once()

    def test_capture_releases_on_open_error(self):
        """``cap.release()`` is NOT called when ``isOpened`` returns ``False``."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False

        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pytest.raises(RuntimeError):
                capture_image("/dev/video0")

        mock_cap.release.assert_not_called()

    def test_custom_device_path(self):
        """The provided device path is passed to ``cv2.VideoCapture``."""
        mock_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)

        with patch("cv2.VideoCapture", return_value=mock_cap) as mock_vc:
            capture_image("/dev/video1")

        mock_vc.assert_called_once_with("/dev/video1")


# ---------------------------------------------------------------------------
# crop_roi
# ---------------------------------------------------------------------------


class TestCropRoi:
    """Tests for :func:`crop_roi`."""

    def test_crop_with_valid_roi(self):
        """The returned slice has the expected shape."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = crop_roi(frame, (20, 10, 100, 50))
        assert result.shape == (50, 100, 3)

    def test_crop_pixel_values_preserved(self):
        """Pixel values inside the ROI are unchanged after cropping."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[10:60, 20:120] = 128
        result = crop_roi(frame, (20, 10, 100, 50))
        assert (result == 128).all()

    def test_crop_zero_width_returns_full_frame(self):
        """Width=0 returns the original frame (full-frame mode)."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = crop_roi(frame, (10, 10, 0, 100))
        assert result is frame

    def test_crop_zero_height_returns_full_frame(self):
        """Height=0 returns the original frame (full-frame mode)."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = crop_roi(frame, (10, 10, 100, 0))
        assert result is frame

    def test_crop_both_zero_returns_full_frame(self):
        """Width=0 and height=0 both return the original frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = crop_roi(frame, (0, 0, 0, 0))
        assert result is frame


# ---------------------------------------------------------------------------
# run_ocr
# ---------------------------------------------------------------------------


class TestRunOcr:
    """Tests for :func:`run_ocr`."""

    def _make_frame(self) -> np.ndarray:
        return np.zeros((100, 200, 3), dtype=np.uint8)

    def test_ocr_returns_stripped_text(self):
        """OCR result is stripped of surrounding whitespace/newlines."""
        frame = self._make_frame()
        with (
            patch("cv2.cvtColor", return_value=frame),
            patch("PIL.Image.fromarray"),
            patch(
                "pytesseract.image_to_string", return_value="  Hello World\n"
            ),
        ):
            result = run_ocr(frame)
        assert result == "Hello World"

    def test_ocr_empty_result(self):
        """Empty OCR result is returned as an empty string."""
        frame = self._make_frame()
        with (
            patch("cv2.cvtColor", return_value=frame),
            patch("PIL.Image.fromarray"),
            patch("pytesseract.image_to_string", return_value="  \n"),
        ):
            result = run_ocr(frame)
        assert result == ""

    def test_ocr_passes_language(self):
        """The ``lang`` parameter is forwarded to pytesseract."""
        frame = self._make_frame()
        with (
            patch("cv2.cvtColor", return_value=frame),
            patch("PIL.Image.fromarray") as mock_pil,
            patch("pytesseract.image_to_string", return_value="text") as mock_ocr,
        ):
            run_ocr(frame, lang="deu")
        mock_ocr.assert_called_once_with(mock_pil.return_value, lang="deu")

    def test_ocr_default_language_is_eng(self):
        """Default language is ``'eng'`` when not specified."""
        frame = self._make_frame()
        with (
            patch("cv2.cvtColor", return_value=frame),
            patch("PIL.Image.fromarray") as mock_pil,
            patch("pytesseract.image_to_string", return_value="text") as mock_ocr,
        ):
            run_ocr(frame)
        mock_ocr.assert_called_once_with(mock_pil.return_value, lang="eng")


# ---------------------------------------------------------------------------
# compare_text
# ---------------------------------------------------------------------------


class TestCompareText:
    """Tests for :func:`compare_text`."""

    def test_single_match(self):
        """A single matching pattern is returned."""
        result = compare_text("Hello World 123", ["World"])
        assert result["is_match"] is True
        assert "World" in result["matched_texts"]

    def test_no_match(self):
        """No match when none of the patterns appear in the text."""
        result = compare_text("Hello World", ["foo", "bar"])
        assert result["is_match"] is False
        assert result["matched_texts"] == []

    def test_case_insensitive(self):
        """Comparison is case-insensitive."""
        result = compare_text("hello world", ["WORLD"])
        assert result["is_match"] is True

    def test_multiple_matches(self):
        """All matching patterns are returned."""
        result = compare_text("hello world test", ["hello", "world", "other"])
        assert result["is_match"] is True
        assert set(result["matched_texts"]) == {"hello", "world"}

    def test_empty_expected_texts(self):
        """Empty list produces no match."""
        result = compare_text("hello world", [])
        assert result["is_match"] is False
        assert result["matched_texts"] == []

    def test_empty_strings_in_list_are_ignored(self):
        """Empty strings in the expected list are skipped (not matched)."""
        result = compare_text("hello world", ["", "world"])
        assert result["is_match"] is True
        assert "" not in result["matched_texts"]

    def test_partial_substring_match(self):
        """A pattern that is a substring of a word is still matched."""
        result = compare_text("temperature=42.5", ["42"])
        assert result["is_match"] is True

    def test_empty_ocr_text(self):
        """Empty OCR text yields no matches."""
        result = compare_text("", ["hello"])
        assert result["is_match"] is False


# ---------------------------------------------------------------------------
# capture_and_analyze  (integration of all helpers)
# ---------------------------------------------------------------------------


class TestCaptureAndAnalyze:
    """End-to-end tests for :func:`capture_and_analyze`."""

    def _make_mocks(self, ocr_output: str):
        """Return a context manager tuple that patches all external I/O."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        return mock_frame, mock_cap, ocr_output

    def test_full_pipeline_with_match(self):
        """Full pipeline returns OCR text and correct match result."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)

        with (
            patch("cv2.VideoCapture", return_value=mock_cap),
            patch("cv2.cvtColor", return_value=mock_frame),
            patch("PIL.Image.fromarray"),
            patch(
                "pytesseract.image_to_string", return_value="METER: 42.5"
            ),
        ):
            result = capture_and_analyze(
                device="/dev/video0",
                roi=(0, 0, 0, 0),
                expected_texts=["42.5", "METER"],
            )

        assert result["ocr_text"] == "METER: 42.5"
        assert result["is_match"] is True
        assert "42.5" in result["matched_texts"]
        assert "METER" in result["matched_texts"]

    def test_full_pipeline_no_match(self):
        """Full pipeline returns is_match=False when text is not found."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)

        with (
            patch("cv2.VideoCapture", return_value=mock_cap),
            patch("cv2.cvtColor", return_value=mock_frame),
            patch("PIL.Image.fromarray"),
            patch("pytesseract.image_to_string", return_value="nothing here"),
        ):
            result = capture_and_analyze(
                device="/dev/video0",
                roi=(0, 0, 0, 0),
                expected_texts=["OPEN", "CLOSED"],
            )

        assert result["ocr_text"] == "nothing here"
        assert result["is_match"] is False
        assert result["matched_texts"] == []

    def test_full_pipeline_with_roi(self):
        """The ROI crop is applied before running OCR."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Place a recognisable value in the ROI region.
        mock_frame[20:120, 10:210] = 200
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)

        with (
            patch("cv2.VideoCapture", return_value=mock_cap),
            patch("cv2.cvtColor", return_value=mock_frame[20:120, 10:210]),
            patch("PIL.Image.fromarray"),
            patch("pytesseract.image_to_string", return_value="42.5"),
        ):
            result = capture_and_analyze(
                device="/dev/video0",
                roi=(10, 20, 200, 100),
                expected_texts=["42.5"],
            )

        assert result["ocr_text"] == "42.5"
        assert result["is_match"] is True

    def test_pipeline_propagates_camera_error(self):
        """RuntimeError from the camera is propagated unchanged."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False

        with patch("cv2.VideoCapture", return_value=mock_cap):
            with pytest.raises(RuntimeError, match="Cannot open camera device"):
                capture_and_analyze(
                    device="/dev/video0",
                    roi=(0, 0, 0, 0),
                    expected_texts=["test"],
                )
