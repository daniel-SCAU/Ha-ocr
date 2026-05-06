"""Sensor platform for the Ha OCR integration.

Two sensor entities are created per config entry:

* **OcrTextSensor** – exposes the raw text extracted by Tesseract OCR as its
  state, with ``match`` and ``matched_texts`` as extra attributes.
* **OcrMatchSensor** – reports ``"match"`` or ``"no_match"`` depending on
  whether the OCR result contains any of the configured expected-text patterns,
  with the full OCR text and matched patterns as extra attributes.
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_MATCH, ATTR_MATCHED_TEXTS, ATTR_OCR_TEXT, DOMAIN
from .coordinator import OcrCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ha OCR sensor entities from a config entry."""
    coordinator: OcrCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            OcrTextSensor(coordinator),
            OcrMatchSensor(coordinator),
        ]
    )


class OcrTextSensor(CoordinatorEntity[OcrCoordinator], SensorEntity):
    """Sensor that reports the raw OCR text result."""

    _attr_has_entity_name = True
    _attr_name = "OCR Text"
    _attr_icon = "mdi:text-recognition"

    def __init__(self, coordinator: OcrCoordinator) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_ocr_text"

    @property
    def device_info(self):  # type: ignore[override]
        """Return shared device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> str | None:
        """Return the OCR-extracted text."""
        if self.coordinator.data:
            return self.coordinator.data.get("ocr_text")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return match result as extra attributes."""
        if self.coordinator.data:
            return {
                ATTR_MATCH: self.coordinator.data.get("is_match", False),
                ATTR_MATCHED_TEXTS: self.coordinator.data.get("matched_texts", []),
            }
        return {}


class OcrMatchSensor(CoordinatorEntity[OcrCoordinator], SensorEntity):
    """Sensor that reports whether the OCR result matches any expected text."""

    _attr_has_entity_name = True
    _attr_name = "OCR Match"
    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, coordinator: OcrCoordinator) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_ocr_match"

    @property
    def device_info(self):  # type: ignore[override]
        """Return shared device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> str | None:
        """Return ``'match'`` or ``'no_match'``."""
        if self.coordinator.data:
            return "match" if self.coordinator.data.get("is_match") else "no_match"
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return OCR text and matched patterns as extra attributes."""
        if self.coordinator.data:
            return {
                ATTR_OCR_TEXT: self.coordinator.data.get("ocr_text", ""),
                ATTR_MATCHED_TEXTS: self.coordinator.data.get("matched_texts", []),
            }
        return {}
