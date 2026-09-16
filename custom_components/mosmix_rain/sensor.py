"""Sensor platform for MOSMIX Rain Predict."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FORECAST_HOURS
from .coordinator import MosmixRainCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MosmixRainCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        MosmixRainProbabilitySensor(coordinator, entry, hours) for hours in FORECAST_HOURS
    )


class MosmixRainProbabilitySensor(CoordinatorEntity[MosmixRainCoordinator], SensorEntity):
    """Rain probability N hours from now (DWD MOSMIX_L, element wwP)."""

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator: MosmixRainCoordinator, entry: ConfigEntry, hours: int) -> None:
        super().__init__(coordinator)
        self._hours = hours
        self._attr_name = f"Regenwahrscheinlichkeit in {hours}h"
        self._attr_unique_id = f"{entry.entry_id}_prob_{hours}h"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "MOSMIX Rain Predict",
            "manufacturer": "Deutscher Wetterdienst (DWD)",
            "model": "MOSMIX_L (wwP)",
        }

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None
        return data["probabilities"][self._hours]["value"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        prob = data["probabilities"][self._hours]
        return {
            "forecast_valid_time": prob["time"].isoformat() if prob["time"] else None,
            "station_id": data["station_id"],
            "station_name": data["station_name"],
            "station_distance_km": data["distance_km"],
            "updated": data["updated"].isoformat(),
        }
