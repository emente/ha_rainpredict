"""Helpers for fetching DWD MOSMIX_L rain-probability forecasts.

Pure, blocking, stdlib-only functions. Callers (the coordinator) are
responsible for running these in an executor.
"""
from __future__ import annotations

import io
import math
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone

STATION_CATALOG_URL = (
    "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/"
    "mosmix_stationskatalog.cfg?view=nasPublication"
)
KMZ_URL_TEMPLATE = (
    "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/"
    "single_stations/{station}/kml/MOSMIX_L_LATEST_{station}.kmz"
)
FORECAST_HOURS = (2, 4, 8)
# wwP: probability of any precipitation within the last hour (general).
# R101/R110: probability of precipitation exceeding 0.1mm / 1.0mm within the last hour.
ELEMENT_NAMES = ("wwP", "R101", "R110")

DWD_NS = "https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd"
NS = {"kml": "http://www.opengis.net/kml/2.2", "dwd": DWD_NS}

USER_AGENT = "ha-mosmix-rain/1.0 (+https://github.com/emente/ha_rainpredict)"


class MosmixError(Exception):
    """Raised when the MOSMIX forecast cannot be fetched or parsed."""


def _download(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as err:  # noqa: BLE001 - normalized into MosmixError
        raise MosmixError(f"Failed to download {url}: {err}") from err


def _parse_dm(value: str) -> float:
    """DWD station catalog uses 'degrees.minutes' (e.g. '52.34' = 52 deg 34 min)."""
    sign = -1.0 if value.startswith("-") else 1.0
    value = value.lstrip("-")
    deg_str, min_str = value.split(".")
    return sign * (int(deg_str) + int(min_str) / 60.0)


def load_station_catalog() -> list[dict]:
    """Download and parse the full DWD MOSMIX station catalog."""
    text = _download(STATION_CATALOG_URL).decode("latin-1")
    stations = []
    for line in text.splitlines()[2:]:  # skip header + separator row
        parts = line.split()
        if len(parts) < 5:
            continue
        station_id = parts[0]
        lat_raw, lon_raw = parts[-3], parts[-2]
        name = " ".join(parts[2:-3])
        try:
            lat, lon = _parse_dm(lat_raw), _parse_dm(lon_raw)
        except ValueError:
            continue
        stations.append({"id": station_id, "name": name, "lat": lat, "lon": lon})
    if not stations:
        raise MosmixError("DWD station catalog is empty or unparsable")
    return stations


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def find_nearest_station(stations: list[dict], lat: float, lon: float) -> dict:
    return min(stations, key=lambda s: _haversine_km(lat, lon, s["lat"], s["lon"]))


def _load_kml(station_id: str) -> bytes:
    url = KMZ_URL_TEMPLATE.format(station=station_id)
    data = _download(url, timeout=30)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            kml_name = next(n for n in zf.namelist() if n.lower().endswith(".kml"))
            return zf.read(kml_name)
    except (zipfile.BadZipFile, StopIteration) as err:
        raise MosmixError(f"Unexpected MOSMIX archive for station {station_id}: {err}") from err


def _parse_forecast(kml_bytes: bytes, station_id: str, element_names: tuple[str, ...]):
    root = ET.fromstring(kml_bytes)
    timesteps = [
        datetime.strptime(ts.text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        for ts in root.findall(".//dwd:ForecastTimeSteps/dwd:TimeStep", NS)
    ]

    placemark = None
    for pm in root.findall(".//kml:Placemark", NS):
        name_el = pm.find("kml:name", NS)
        if name_el is not None and name_el.text.strip() == station_id:
            placemark = pm
            break
    if placemark is None:
        raise MosmixError(f"Station {station_id} not found in MOSMIX KML")

    remaining = set(element_names)
    values_by_element: dict[str, list[str]] = {}
    for forecast in placemark.findall(".//dwd:Forecast", NS):
        name = forecast.get(f"{{{DWD_NS}}}elementName")
        if name in remaining:
            values_by_element[name] = forecast.find("dwd:value", NS).text.split()
            remaining.discard(name)
            if not remaining:
                break
    if remaining:
        raise MosmixError(f"Elements {sorted(remaining)} not present for station {station_id}")
    for name, values in values_by_element.items():
        if len(values) != len(timesteps):
            raise MosmixError(f"Timestep/value count mismatch for {name} in MOSMIX KML")
    return timesteps, values_by_element


def _combine_probabilities(hourly_values: list[int | None]) -> int | None:
    """Combine independent hourly rain-probabilities into "at least one hour rains".

    Uses the standard 1 - prod(1 - p_i) formula, which assumes the hourly
    outcomes are independent. Real weather is autocorrelated (rain in one
    hour makes rain in the next more, not less, likely), so this tends to
    slightly *overestimate* the true joint probability. It is nonetheless
    the closest approximation obtainable from MOSMIX's per-hour values,
    since DWD does not publish a native 2h/4h/8h cumulative element.
    """
    if not hourly_values or any(v is None for v in hourly_values):
        return None
    no_rain_at_all = 1.0
    for v in hourly_values:
        no_rain_at_all *= 1 - v / 100.0
    return round((1 - no_rain_at_all) * 100)


def _window_probability(timesteps, values, now, hours):
    """Probability that the event occurs at least once in the next `hours` hours.

    Combines the hourly buckets strictly after `now`, i.e. timesteps
    (now, now+hours] on the hourly grid - up to ~1h of look-back overlap
    with the present is inherent to hourly-resolution source data.
    """
    start_idx = next((i for i, t in enumerate(timesteps) if t > now), None)
    if start_idx is None:
        return None, [], None
    window_idx = range(start_idx, min(start_idx + hours, len(timesteps)))
    window_idx = list(window_idx)
    if len(window_idx) < hours:
        return None, [], None  # forecast horizon too short (stale/delayed run)

    hourly_values = [None if values[i] == "-" else round(float(values[i])) for i in window_idx]
    combined = _combine_probabilities(hourly_values)
    window_end = timesteps[window_idx[-1]]
    return combined, hourly_values, window_end


def fetch_rain_forecast(
    stations: list[dict],
    latitude: float,
    longitude: float,
    element_names: tuple[str, ...] = ELEMENT_NAMES,
    forecast_hours: tuple[int, ...] = FORECAST_HOURS,
) -> dict:
    """Fetch, for the nearest station, the probability of the event occurring
    at least once within the next 2/4/8 hours (not a single-hour snapshot).
    """
    station = find_nearest_station(stations, latitude, longitude)
    kml_bytes = _load_kml(station["id"])
    timesteps, values_by_element = _parse_forecast(kml_bytes, station["id"], element_names)

    now = datetime.now(timezone.utc)
    result = {
        "station_id": station["id"],
        "station_name": station["name"],
        "station_lat": round(station["lat"], 4),
        "station_lon": round(station["lon"], 4),
        "distance_km": round(_haversine_km(latitude, longitude, station["lat"], station["lon"]), 1),
        "updated": now,
        "elements": {},
    }
    for element in element_names:
        values = values_by_element[element]
        by_window = {}
        for hours in forecast_hours:
            combined, hourly_values, window_end = _window_probability(timesteps, values, now, hours)
            by_window[hours] = {
                "value": combined,
                "hourly_values": hourly_values,
                "window_end": window_end,
            }
        result["elements"][element] = by_window
    return result
