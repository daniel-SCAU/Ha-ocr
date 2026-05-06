"""Button platform for the Ha OCR integration.

A single :class:`OcrCaptureButton` entity is created per config entry.
Pressing it triggers an OCR capture cycle (the same action as calling the
``ha_ocr.capture`` service).
"""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OcrCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ha OCR button entities from a config entry."""
    coordinator: OcrCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OcrCaptureButton(coordinator)])


class OcrCaptureButton(CoordinatorEntity[OcrCoordinator], ButtonEntity):
    """Button that triggers an OCR capture when pressed."""

    _attr_has_entity_name = True
    _attr_name = "Capture"
    _attr_icon = "mdi:camera"

    def __init__(self, coordinator: OcrCoordinator) -> None:
        """Initialise the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_capture"

    @property
    def device_info(self):  # type: ignore[override]
        """Return shared device info."""
        return self.coordinator.device_info

    async def async_press(self) -> None:
        """Handle button press: trigger an OCR capture cycle."""
        await self.coordinator.async_request_refresh()
