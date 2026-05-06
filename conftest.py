"""Root conftest – inject minimal homeassistant stubs so that integration
modules can be imported without a full HA installation.

Only the symbols actually referenced by the integration source files are
stubbed out here; everything else can stay as a bare module.
"""
from __future__ import annotations

import sys
import types


def _make_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ---------------------------------------------------------------------------
# Build the module tree first so attribute access on parent packages works.
# ---------------------------------------------------------------------------
for _name in [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.helpers",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.device_registry",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.button",
]:
    _make_module(_name)

# Patch parent packages so child attribute lookups succeed.
sys.modules["homeassistant"].config_entries = sys.modules["homeassistant.config_entries"]
sys.modules["homeassistant"].core = sys.modules["homeassistant.core"]
sys.modules["homeassistant"].helpers = sys.modules["homeassistant.helpers"]
sys.modules["homeassistant"].components = sys.modules["homeassistant.components"]
sys.modules["homeassistant.helpers"].entity_platform = sys.modules[
    "homeassistant.helpers.entity_platform"
]
sys.modules["homeassistant.helpers"].update_coordinator = sys.modules[
    "homeassistant.helpers.update_coordinator"
]
sys.modules["homeassistant.helpers"].device_registry = sys.modules[
    "homeassistant.helpers.device_registry"
]
sys.modules["homeassistant.components"].sensor = sys.modules[
    "homeassistant.components.sensor"
]
sys.modules["homeassistant.components"].button = sys.modules[
    "homeassistant.components.button"
]

# ---------------------------------------------------------------------------
# homeassistant.config_entries
# ---------------------------------------------------------------------------
_ce = sys.modules["homeassistant.config_entries"]


class _ConfigEntry:
    def __init__(self, entry_id: str = "test_entry_id", data: dict | None = None):
        self.entry_id = entry_id
        self.data = data or {}


class _ConfigFlow:
    def __init_subclass__(cls, domain: str = "", **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def async_get_options_flow(cls, config_entry):  # noqa: D401
        return None


class _OptionsFlow:
    pass


class _FlowResult(dict):
    pass


_ce.ConfigEntry = _ConfigEntry
_ce.ConfigFlow = _ConfigFlow
_ce.OptionsFlow = _OptionsFlow
_ce.FlowResult = _FlowResult

# ---------------------------------------------------------------------------
# homeassistant.core
# ---------------------------------------------------------------------------
_core = sys.modules["homeassistant.core"]


class _HomeAssistant:
    pass


class _ServiceCall:
    def __init__(self, data: dict | None = None):
        self.data = data or {}


_core.HomeAssistant = _HomeAssistant
_core.ServiceCall = _ServiceCall
_core.callback = lambda func: func  # decorator pass-through

# ---------------------------------------------------------------------------
# homeassistant.helpers.update_coordinator
# ---------------------------------------------------------------------------
_uc = sys.modules["homeassistant.helpers.update_coordinator"]


class _DataUpdateCoordinator:
    def __init__(self, hass, logger, *, name, update_interval=None):
        self.hass = hass
        self.name = name
        self.data = None
        self.listeners: list = []

    def __class_getitem__(cls, item):  # makes DataUpdateCoordinator[T] valid
        return cls

    async def async_request_refresh(self):
        self.data = await self._async_update_data()
        for listener in self.listeners:
            listener()

    async def _async_update_data(self):
        return {}


class _CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class _UpdateFailed(Exception):
    pass


_uc.DataUpdateCoordinator = _DataUpdateCoordinator
_uc.CoordinatorEntity = _CoordinatorEntity
_uc.UpdateFailed = _UpdateFailed

# ---------------------------------------------------------------------------
# homeassistant.helpers.device_registry
# ---------------------------------------------------------------------------
_dr = sys.modules["homeassistant.helpers.device_registry"]


class _DeviceInfo(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


_dr.DeviceInfo = _DeviceInfo

# ---------------------------------------------------------------------------
# homeassistant.helpers.entity_platform
# ---------------------------------------------------------------------------
_ep = sys.modules["homeassistant.helpers.entity_platform"]
_ep.AddEntitiesCallback = object  # type alias – not instantiated in tests

# ---------------------------------------------------------------------------
# homeassistant.components.sensor
# ---------------------------------------------------------------------------
_sensor = sys.modules["homeassistant.components.sensor"]


class _SensorEntity:
    pass


_sensor.SensorEntity = _SensorEntity

# ---------------------------------------------------------------------------
# homeassistant.components.button
# ---------------------------------------------------------------------------
_button = sys.modules["homeassistant.components.button"]


class _ButtonEntity:
    pass


_button.ButtonEntity = _ButtonEntity
