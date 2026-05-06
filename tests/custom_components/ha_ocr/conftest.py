"""Shared fixtures for ha_ocr tests."""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_config_entry_data() -> dict:
    """Return a minimal valid config-entry data dict."""
    return {
        "device": "/dev/video0",
        "roi_x": 0,
        "roi_y": 0,
        "roi_width": 0,
        "roi_height": 0,
        "expected_texts": "OPEN,CLOSED",
        "ocr_lang": "eng",
    }


@pytest.fixture
def mock_config_entry_data_with_roi() -> dict:
    """Return a config-entry data dict with a non-zero ROI."""
    return {
        "device": "/dev/video0",
        "roi_x": 10,
        "roi_y": 20,
        "roi_width": 200,
        "roi_height": 100,
        "expected_texts": "42.5",
        "ocr_lang": "eng",
    }
