"""Constants for the MOSMIX Rain Predict integration."""

DOMAIN = "mosmix_rain"
UPDATE_INTERVAL_MINUTES = 30
FORECAST_HOURS = (2, 4, 8)

BEAUFORT_NAMES = (
    "Windstille",
    "leiser Zug",
    "leichte Brise",
    "schwache Brise",
    "mäßige Brise",
    "frische Brise",
    "starker Wind",
    "steifer Wind",
    "stürmischer Wind",
    "Sturm",
    "schwerer Sturm",
    "orkanartiger Sturm",
    "Orkan",
)

# Display metadata for the DWD MOSMIX elements exposed as sensors.
# "code" must match a key of dwd_mosmix.ELEMENT_KINDS.
ELEMENTS = (
    {
        "code": "wwP",
        "unique_id": "prob",
        "name": "Regenwahrscheinlichkeit",
        "icon": "mdi:weather-rainy",
        "unit": "%",
        "device_class": None,
    },
    {
        "code": "R101",
        "unique_id": "prob_r101",
        "name": "Regenwahrscheinlichkeit >0,1mm",
        "icon": "mdi:weather-rainy",
        "unit": "%",
        "device_class": None,
    },
    {
        "code": "R110",
        "unique_id": "prob_r110",
        "name": "Regenwahrscheinlichkeit >1,0mm",
        "icon": "mdi:weather-pouring",
        "unit": "%",
        "device_class": None,
    },
    {
        "code": "FF",
        "unique_id": "wind_max",
        "name": "Höchste Windgeschwindigkeit",
        "icon": "mdi:weather-windy",
        "unit": "m/s",
        "device_class": "wind_speed",
    },
    {
        "code": "FX1",
        "unique_id": "gust_max",
        "name": "Höchste Windböe",
        "icon": "mdi:weather-windy-variant",
        "unit": "m/s",
        "device_class": "wind_speed",
    },
)
