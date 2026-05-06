"""Unit tests for the config-flow validation helper."""
from __future__ import annotations

import pytest

from custom_components.ha_ocr.config_flow import _validate_roi
from custom_components.ha_ocr.const import (
    CONF_ROI_HEIGHT,
    CONF_ROI_WIDTH,
    CONF_ROI_X,
    CONF_ROI_Y,
)


class TestValidateRoi:
    """Tests for the ``_validate_roi`` helper used in the config flow."""

    def test_valid_zero_roi(self):
        """All-zero ROI (full-frame mode) is valid."""
        data = {CONF_ROI_X: 0, CONF_ROI_Y: 0, CONF_ROI_WIDTH: 0, CONF_ROI_HEIGHT: 0}
        assert _validate_roi(data) == {}

    def test_valid_positive_roi(self):
        """Positive ROI coordinates are valid."""
        data = {
            CONF_ROI_X: 10,
            CONF_ROI_Y: 20,
            CONF_ROI_WIDTH: 200,
            CONF_ROI_HEIGHT: 100,
        }
        assert _validate_roi(data) == {}

    def test_negative_roi_x(self):
        """Negative ``roi_x`` produces an error on that field."""
        data = {
            CONF_ROI_X: -1,
            CONF_ROI_Y: 0,
            CONF_ROI_WIDTH: 100,
            CONF_ROI_HEIGHT: 50,
        }
        errors = _validate_roi(data)
        assert CONF_ROI_X in errors
        assert errors[CONF_ROI_X] == "roi_negative"

    def test_negative_roi_y(self):
        """Negative ``roi_y`` produces an error on that field."""
        data = {
            CONF_ROI_X: 0,
            CONF_ROI_Y: -5,
            CONF_ROI_WIDTH: 100,
            CONF_ROI_HEIGHT: 50,
        }
        errors = _validate_roi(data)
        assert CONF_ROI_Y in errors

    def test_negative_roi_width(self):
        """Negative ``roi_width`` produces an error on that field."""
        data = {
            CONF_ROI_X: 0,
            CONF_ROI_Y: 0,
            CONF_ROI_WIDTH: -10,
            CONF_ROI_HEIGHT: 50,
        }
        errors = _validate_roi(data)
        assert CONF_ROI_WIDTH in errors

    def test_negative_roi_height(self):
        """Negative ``roi_height`` produces an error on that field."""
        data = {
            CONF_ROI_X: 0,
            CONF_ROI_Y: 0,
            CONF_ROI_WIDTH: 100,
            CONF_ROI_HEIGHT: -20,
        }
        errors = _validate_roi(data)
        assert CONF_ROI_HEIGHT in errors

    def test_only_one_error_reported_at_a_time(self):
        """At most one field error is reported per validation call."""
        data = {
            CONF_ROI_X: -1,
            CONF_ROI_Y: -1,
            CONF_ROI_WIDTH: -1,
            CONF_ROI_HEIGHT: -1,
        }
        errors = _validate_roi(data)
        assert len(errors) == 1
