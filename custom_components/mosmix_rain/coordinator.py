"""DataUpdateCoordinator for the MOSMIX Rain Predict integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL_MINUTES
from .dwd_mosmix import MosmixError, fetch_rain_forecast, load_station_catalog

_LOGGER = logging.getLogger(__name__)


class MosmixRainCoordinator(DataUpdateCoordinator[dict]):
    """Coordinates fetching MOSMIX rain-probability data for one location."""

    def __init__(self, hass: HomeAssistant, latitude: float, longitude: float) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.latitude = latitude
        self.longitude = longitude
        self._stations: list[dict] | None = None

    def _fetch(self) -> dict:
        if self._stations is None:
            self._stations = load_station_catalog()
        try:
            return fetch_rain_forecast(self._stations, self.latitude, self.longitude)
        except MosmixError:
            # Retry once with a freshly downloaded station catalog, in case
            # a station id disappeared from the DWD catalog in the meantime.
            self._stations = load_station_catalog()
            return fetch_rain_forecast(self._stations, self.latitude, self.longitude)

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except MosmixError as err:
            raise UpdateFailed(str(err)) from err
