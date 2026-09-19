"""Config and options flow for MOSMIX Rain Predict."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .dwd_mosmix import MosmixError, fetch_forecast, load_station_catalog

_LOGGER = logging.getLogger(__name__)


def _coordinate_schema(default_lat: float, default_lon: float) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("latitude", default=default_lat): vol.Coerce(float),
            vol.Required("longitude", default=default_lon): vol.Coerce(float),
        }
    )


async def _validate_coordinates(hass: HomeAssistant, latitude: float, longitude: float) -> dict:
    """Fetch a forecast for the given coordinates, raising MosmixError on failure."""
    stations = await hass.async_add_executor_job(load_station_catalog)
    return await hass.async_add_executor_job(fetch_forecast, stations, latitude, longitude)


class MosmixRainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MOSMIX Rain Predict."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        if user_input is not None:
            latitude = user_input["latitude"]
            longitude = user_input["longitude"]
            try:
                result = await _validate_coordinates(self.hass, latitude, longitude)
            except MosmixError:
                _LOGGER.exception("Could not validate MOSMIX coordinates")
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{latitude:.4f}_{longitude:.4f}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"MOSMIX Rain ({result['station_name']})",
                    data={"latitude": latitude, "longitude": longitude},
                )

        return self.async_show_form(
            step_id="user", data_schema=_coordinate_schema(default_lat, default_lon), errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MosmixRainOptionsFlow:
        return MosmixRainOptionsFlow(config_entry)


class MosmixRainOptionsFlow(config_entries.OptionsFlow):
    """Let the user change the configured coordinates after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors: dict[str, str] = {}

        default_lat = self.config_entry.options.get(
            "latitude", self.config_entry.data["latitude"]
        )
        default_lon = self.config_entry.options.get(
            "longitude", self.config_entry.data["longitude"]
        )

        if user_input is not None:
            latitude = user_input["latitude"]
            longitude = user_input["longitude"]
            try:
                await _validate_coordinates(self.hass, latitude, longitude)
            except MosmixError:
                _LOGGER.exception("Could not validate MOSMIX coordinates")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="", data={"latitude": latitude, "longitude": longitude}
                )

        return self.async_show_form(
            step_id="init", data_schema=_coordinate_schema(default_lat, default_lon), errors=errors
        )
