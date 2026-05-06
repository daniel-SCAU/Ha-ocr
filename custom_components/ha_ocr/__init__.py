"""The Ha OCR custom integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, PLATFORMS, SERVICE_CAPTURE
from .coordinator import OcrCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ha OCR from a config entry.

    Creates an :class:`OcrCoordinator`, forwards platform setup, and registers
    the ``ha_ocr.capture`` service (only once, even across multiple entries).
    """
    coordinator = OcrCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the capture service only the first time an entry is loaded.
    if not hass.services.has_service(DOMAIN, SERVICE_CAPTURE):

        async def _handle_capture(call: ServiceCall) -> None:
            """Trigger OCR capture for one or all configured entries."""
            entry_id: str | None = call.data.get("entry_id")
            if entry_id:
                coord = hass.data[DOMAIN].get(entry_id)
                if coord is None:
                    _LOGGER.warning(
                        "ha_ocr.capture: no entry found with id '%s'", entry_id
                    )
                    return
                await coord.async_request_refresh()
            else:
                for coord in list(hass.data[DOMAIN].values()):
                    await coord.async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_CAPTURE, _handle_capture)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up shared resources."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove the service only when the last entry is unloaded.
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_CAPTURE)
            hass.data.pop(DOMAIN)
    return unload_ok
