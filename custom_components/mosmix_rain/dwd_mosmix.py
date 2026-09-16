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
from datetime import datetime, timedelta, timezone

STATION_CATALOG_URL = (
    "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/"
    "mosmix_stationskatalog.cfg?view=nasPublication"
)
KMZ_URL_TEMPLATE = (
    "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/"
    "single_stations/{station}/kml/MOSMIX_L_LATEST_{station}.kmz"
)
FORECAST_HOURS = (2, 4, 8)
ELEMENT_NAME = "wwP"  # general probability of precipitation (%), hourly

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


def _parse_forecast(kml_bytes: bytes, station_id: str, element_name: str):
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

    values = None
    for forecast in placemark.findall(".//dwd:Forecast", NS):
        if forecast.get(f"{{{DWD_NS}}}elementName") == element_name:
            values = forecast.find("dwd:value", NS).text.split()
            break
    if values is None:
        raise MosmixError(f"Element {element_name} not present for station {station_id}")
    if len(values) != len(timesteps):
        raise MosmixError("Timestep/value count mismatch in MOSMIX KML")
    return timesteps, values


def _nearest_value(timesteps, values, target):
    idx = min(range(len(timesteps)), key=lambda i: abs((timesteps[i] - target).total_seconds()))
    raw = values[idx]
    value = None if raw == "-" else round(float(raw))
    return value, timesteps[idx]


def fetch_rain_forecast(stations: list[dict], latitude: float, longitude: float) -> dict:
    """Fetch the current MOSMIX_L rain-probability forecast for the nearest station."""
    station = find_nearest_station(stations, latitude, longitude)
    kml_bytes = _load_kml(station["id"])
    timesteps, values = _parse_forecast(kml_bytes, station["id"], ELEMENT_NAME)

    now = datetime.now(timezone.utc)
    result = {
        "station_id": station["id"],
        "station_name": station["name"],
        "station_lat": round(station["lat"], 4),
        "station_lon": round(station["lon"], 4),
        "distance_km": round(_haversine_km(latitude, longitude, station["lat"], station["lon"]), 1),
        "updated": now,
        "probabilities": {},
    }
    for hours in FORECAST_HOURS:
        prob, matched_time = _nearest_value(timesteps, values, now + timedelta(hours=hours))
        result["probabilities"][hours] = {"value": prob, "time": matched_time}
    return result
