"""Data update coordinator for the Ha OCR integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE,
    CONF_EXPECTED_TEXTS,
    CONF_OCR_LANG,
    CONF_ROI_HEIGHT,
    CONF_ROI_WIDTH,
    CONF_ROI_X,
    CONF_ROI_Y,
    DEFAULT_OCR_LANG,
    DOMAIN,
)
from .ocr import capture_and_analyze

_LOGGER = logging.getLogger(__name__)


class OcrCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage trigger-based OCR capture and distribute data to entities.

    ``update_interval`` is intentionally ``None`` so no automatic polling
    occurs.  Refreshes are triggered either by:
      - Pressing the *Capture* button entity, or
      - Calling the ``ha_ocr.capture`` service.
    """

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator from a config entry."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # manual / trigger-based only
        )
        self.config_entry = entry
        self.device: str = entry.data[CONF_DEVICE]
        self.roi: tuple[int, int, int, int] = (
            entry.data[CONF_ROI_X],
            entry.data[CONF_ROI_Y],
            entry.data[CONF_ROI_WIDTH],
            entry.data[CONF_ROI_HEIGHT],
        )
        self.ocr_lang: str = entry.data.get(CONF_OCR_LANG, DEFAULT_OCR_LANG)
        self.expected_texts: list[str] = [
            t.strip()
            for t in entry.data.get(CONF_EXPECTED_TEXTS, "").split(",")
            if t.strip()
        ]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information shared by all entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=f"OCR Camera ({self.device})",
            manufacturer="USB Camera",
            model="Video4Linux (V4L2)",
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Execute the blocking capture-and-analyse pipeline in a thread pool."""
        try:
            return await self.hass.async_add_executor_job(
                capture_and_analyze,
                self.device,
                self.roi,
                self.expected_texts,
                self.ocr_lang,
            )
        except RuntimeError as err:
            raise UpdateFailed(f"OCR capture failed: {err}") from err
