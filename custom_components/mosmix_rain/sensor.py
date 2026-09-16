"""Sensor platform for MOSMIX Rain Predict."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ELEMENTS, FORECAST_HOURS
from .coordinator import MosmixRainCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MosmixRainCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        MosmixRainProbabilitySensor(coordinator, entry, element, hours)
        for element in ELEMENTS
        for hours in FORECAST_HOURS
    ]
    async_add_entities(entities)


class MosmixRainProbabilitySensor(CoordinatorEntity[MosmixRainCoordinator], SensorEntity):
    """Probability that the event occurs at least once within the next N hours.

    This is a combined ("at least one of the next N hourly buckets rains")
    probability, not a single-hour snapshot N hours from now - see
    dwd_mosmix._combine_probabilities for the exact formula and its caveats.
    """

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: MosmixRainCoordinator,
        entry: ConfigEntry,
        element: dict,
        hours: int,
    ) -> None:
        super().__init__(coordinator)
        self._code = element["code"]
        self._hours = hours
        self._attr_name = f"{element['name']} innerhalb {hours}h"
        self._attr_icon = element["icon"]
        self._attr_unique_id = f"{entry.entry_id}_{element['unique_id']}_{hours}h"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "MOSMIX Rain Predict",
            "manufacturer": "Deutscher Wetterdienst (DWD)",
            "model": "MOSMIX_L",
        }

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None
        return data["elements"][self._code][self._hours]["value"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        window = data["elements"][self._code][self._hours]
        return {
            "element": self._code,
            "window_hours": self._hours,
            "window_end": window["window_end"].isoformat() if window["window_end"] else None,
            "hourly_values": window["hourly_values"],
            "station_id": data["station_id"],
            "station_name": data["station_name"],
            "station_distance_km": data["distance_km"],
            "updated": data["updated"].isoformat(),
        }
