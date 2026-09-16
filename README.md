# MOSMIX Rain Predict

Home Assistant custom integration that provides rain-probability sensors
sourced directly from the German Weather Service's (DWD) **MOSMIX_L**
forecast — no third-party weather API in between.

## What it does

- Downloads the official DWD MOSMIX station catalog and finds the nearest
  forecast station to a location you configure through the UI.
- Downloads that station's MOSMIX_L forecast (KMZ/KML) directly from
  `opendata.dwd.de`.
- Reads the `wwP` element (general probability of precipitation, %,
  hourly resolution) and exposes three sensors:
  - **Regenwahrscheinlichkeit in 2h**
  - **Regenwahrscheinlichkeit in 4h**
  - **Regenwahrscheinlichkeit in 8h**
- Refreshes every 30 minutes (DWD publishes a new MOSMIX_L run every 6
  hours).

Each sensor exposes the DWD station id/name/distance and the exact
forecast-valid timestamp as attributes.

## Installation via HACS

1. In Home Assistant, go to **HACS → ⋮ → Custom repositories**.
2. Add this repository's URL with category **Integration**.
3. Install **MOSMIX Rain Predict**, then restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration**, search for
   **MOSMIX Rain Predict**.
5. Confirm or adjust the latitude/longitude (defaults to your Home
   Assistant location) and submit.

The location is only read once at setup time. To move the sensors to a
different location, remove and re-add the integration with new
coordinates.

## Data source & attribution

Forecast data: Deutscher Wetterdienst (DWD), MOSMIX_L, via
[opendata.dwd.de](https://opendata.dwd.de). No API key required, no
affiliation with DWD.

## Limitations

- `wwP` is DWD's general precipitation-probability element; it is not
  threshold-specific (compare to `R101`, `R110`, etc. for probability of
  exceeding a specific mm/h amount).
- Coordinates are fixed at setup (no options flow yet) — reconfigure by
  removing and re-adding the integration.
