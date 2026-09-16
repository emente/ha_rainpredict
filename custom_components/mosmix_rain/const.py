"""Constants for the MOSMIX Rain Predict integration."""

DOMAIN = "mosmix_rain"
UPDATE_INTERVAL_MINUTES = 30
FORECAST_HOURS = (2, 4, 8)

# Display metadata for the DWD MOSMIX elements exposed as sensors.
# "code" must match custom_components/mosmix_rain/dwd_mosmix.py ELEMENT_NAMES.
ELEMENTS = (
    {
        "code": "wwP",
        "unique_id": "prob",
        "name": "Regenwahrscheinlichkeit",
        "icon": "mdi:weather-rainy",
    },
    {
        "code": "R101",
        "unique_id": "prob_r101",
        "name": "Regenwahrscheinlichkeit >0,1mm",
        "icon": "mdi:weather-rainy",
    },
    {
        "code": "R110",
        "unique_id": "prob_r110",
        "name": "Regenwahrscheinlichkeit >1,0mm",
        "icon": "mdi:weather-pouring",
    },
)
