"""Config flow for MOSMIX Rain Predict."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN
from .dwd_mosmix import MosmixError, fetch_rain_forecast, load_station_catalog

_LOGGER = logging.getLogger(__name__)


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
                stations = await self.hass.async_add_executor_job(load_station_catalog)
                result = await self.hass.async_add_executor_job(
                    fetch_rain_forecast, stations, latitude, longitude
                )
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

        schema = vol.Schema(
            {
                vol.Required("latitude", default=default_lat): vol.Coerce(float),
                vol.Required("longitude", default=default_lon): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
