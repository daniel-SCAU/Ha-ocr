"""Config flow for the Ha OCR integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_DEVICE,
    CONF_EXPECTED_TEXTS,
    CONF_OCR_LANG,
    CONF_ROI_HEIGHT,
    CONF_ROI_WIDTH,
    CONF_ROI_X,
    CONF_ROI_Y,
    DEFAULT_DEVICE,
    DEFAULT_EXPECTED_TEXTS,
    DEFAULT_OCR_LANG,
    DEFAULT_ROI_HEIGHT,
    DEFAULT_ROI_WIDTH,
    DEFAULT_ROI_X,
    DEFAULT_ROI_Y,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE, default=DEFAULT_DEVICE): str,
        vol.Required(CONF_ROI_X, default=DEFAULT_ROI_X): vol.Coerce(int),
        vol.Required(CONF_ROI_Y, default=DEFAULT_ROI_Y): vol.Coerce(int),
        vol.Required(CONF_ROI_WIDTH, default=DEFAULT_ROI_WIDTH): vol.Coerce(int),
        vol.Required(CONF_ROI_HEIGHT, default=DEFAULT_ROI_HEIGHT): vol.Coerce(int),
        vol.Optional(CONF_EXPECTED_TEXTS, default=DEFAULT_EXPECTED_TEXTS): str,
        vol.Optional(CONF_OCR_LANG, default=DEFAULT_OCR_LANG): str,
    }
)


def _validate_roi(data: dict) -> dict[str, str]:
    """Return a dict of field-level errors for negative ROI values."""
    errors: dict[str, str] = {}
    for field in (CONF_ROI_X, CONF_ROI_Y, CONF_ROI_WIDTH, CONF_ROI_HEIGHT):
        if data.get(field, 0) < 0:
            errors[field] = "roi_negative"
            break  # report one error at a time for clarity
    return errors


class HaOcrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration flow for Ha OCR."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the user-facing setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_roi(user_input)
            if not errors:
                device = user_input[CONF_DEVICE]
                return self.async_create_entry(
                    title=f"OCR Camera ({device})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HaOcrOptionsFlow:
        """Return the options flow handler."""
        return HaOcrOptionsFlow(config_entry)


class HaOcrOptionsFlow(config_entries.OptionsFlow):
    """Allow updating device, ROI and expected-text settings after initial setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Store the config entry for later use."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Present the options form and handle submission."""
        errors: dict[str, str] = {}
        current = self.config_entry.data

        if user_input is not None:
            errors = _validate_roi(user_input)
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**current, **user_input},
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE, default=current.get(CONF_DEVICE, DEFAULT_DEVICE)
                    ): str,
                    vol.Required(
                        CONF_ROI_X, default=current.get(CONF_ROI_X, DEFAULT_ROI_X)
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_ROI_Y, default=current.get(CONF_ROI_Y, DEFAULT_ROI_Y)
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_ROI_WIDTH,
                        default=current.get(CONF_ROI_WIDTH, DEFAULT_ROI_WIDTH),
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_ROI_HEIGHT,
                        default=current.get(CONF_ROI_HEIGHT, DEFAULT_ROI_HEIGHT),
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_EXPECTED_TEXTS,
                        default=current.get(CONF_EXPECTED_TEXTS, DEFAULT_EXPECTED_TEXTS),
                    ): str,
                    vol.Optional(
                        CONF_OCR_LANG,
                        default=current.get(CONF_OCR_LANG, DEFAULT_OCR_LANG),
                    ): str,
                }
            ),
            errors=errors,
        )
