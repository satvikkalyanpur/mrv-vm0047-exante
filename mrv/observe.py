"""Observed record for the plot, from free services that need no login.

- Rainfall and temperature: NASA POWER daily point data (about 50 km grid).
- Greenness: MODIS MOD13Q1 NDVI, one 250 m pixel every 16 days, from the
  ORNL DAAC subset service.

Both are coarser than the 1.27 ha parcel. They describe the plot's
surroundings, not individual palms; the 10 m Sentinel-2 view is in the
notebook's optional Earth Engine cell.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime

import pandas as pd

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MODIS_URL = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
MODIS_BAND = "250m_16_days_NDVI"
MODIS_FILL = -3000
POWER_FILL = -999.0


def parcel_centroid(geojson_path: str) -> tuple[float, float]:
    """(latitude, longitude) of the polygon's vertex mean."""
    with open(geojson_path, encoding="utf-8") as f:
        ring = json.load(f)["features"][0]["geometry"]["coordinates"][0][:-1]
    return sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)


# ---- parsing (pure functions, covered by tests) --------------------------

def parse_power_daily(payload: dict) -> pd.DataFrame:
    """NASA POWER daily JSON -> one row per month with rainfall (mm) and mean
    temperature (deg C). Days with the fill value are dropped."""
    params = payload["properties"]["parameter"]
    rain = pd.Series(params["PRECTOTCORR"], dtype=float)
    temp = pd.Series(params["T2M"], dtype=float)
    df = pd.DataFrame({"rain_mm": rain, "temp_c": temp})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.where(df > POWER_FILL + 1)
    monthly = pd.DataFrame({
        "rain_mm": df.rain_mm.resample("MS").sum(min_count=1),
        "temp_c": df.temp_c.resample("MS").mean(),
        "days_with_data": df.rain_mm.resample("MS").count(),
    })
    monthly.index.name = "month"
    return monthly.reset_index()


def parse_modis_subset(payload: dict) -> list[dict]:
    """ORNL MODIS subset JSON -> rows of (date, ndvi). Fill values are dropped."""
    scale = float(payload.get("scale") or 0.0001)
    rows = []
    for item in payload.get("subset", []):
        raw = item["data"][0]
        if raw is None or raw <= MODIS_FILL:
            continue
        rows.append({"date": item["calendar_date"], "ndvi": round(raw * scale, 4)})
    return rows


def _modis_date(d: date) -> str:
    return f"A{d.year}{d.timetuple().tm_yday:03d}"


# ---- network calls --------------------------------------------------------

def fetch_weather(lat: float, lon: float, start: date, end: date, timeout: int = 60) -> pd.DataFrame:
    import requests
    r = requests.get(POWER_URL, timeout=timeout, params={
        "parameters": "PRECTOTCORR,T2M", "community": "AG", "latitude": lat, "longitude": lon,
        "start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"), "format": "JSON",
    })
    r.raise_for_status()
    return parse_power_daily(r.json())


def fetch_ndvi(lat: float, lon: float, start: date, end: date, timeout: int = 60) -> pd.DataFrame:
    """The service returns at most ten dates per request, so ask in chunks."""
    import requests
    headers = {"Accept": "application/json"}
    r = requests.get(f"{MODIS_URL}/dates", params={"latitude": lat, "longitude": lon},
                     headers=headers, timeout=timeout)
    r.raise_for_status()
    wanted = [d["modis_date"] for d in r.json()["dates"]
              if start <= datetime.strptime(d["calendar_date"], "%Y-%m-%d").date() <= end]
    rows = []
    for i in range(0, len(wanted), 10):
        chunk = wanted[i:i + 10]
        r = requests.get(f"{MODIS_URL}/subset", headers=headers, timeout=timeout, params={
            "latitude": lat, "longitude": lon, "band": MODIS_BAND,
            "startDate": chunk[0], "endDate": chunk[-1], "kmAboveBelow": 0, "kmLeftRight": 0,
        })
        r.raise_for_status()
        rows += parse_modis_subset(r.json())
    return pd.DataFrame(rows, columns=["date", "ndvi"])


def collect(geojson_path: str, out_dir: str, start: date, end: date) -> dict:
    """Fetch both records and save them as CSV. Each service is tried on its
    own, so one failing does not lose the other."""
    lat, lon = parcel_centroid(geojson_path)
    os.makedirs(out_dir, exist_ok=True)
    report = {"latitude": round(lat, 5), "longitude": round(lon, 5)}
    for name, fetch in (("weather_nasa_power.csv", fetch_weather), ("ndvi_modis_250m.csv", fetch_ndvi)):
        try:
            df = fetch(lat, lon, start, end)
            df.to_csv(os.path.join(out_dir, name), index=False)
            report[name] = f"{len(df)} rows"
        except Exception as exc:  # network or format problem: report it, keep going
            report[name] = f"FAILED: {type(exc).__name__}: {exc}"
    return report


def load(out_dir: str) -> dict[str, pd.DataFrame]:
    """Whatever observed files exist, keyed by short name."""
    found = {}
    for key, name in (("weather", "weather_nasa_power.csv"), ("ndvi_modis", "ndvi_modis_250m.csv"),
                      ("ndvi_sentinel2", "ndvi_sentinel2_10m.csv"), ("ndvi_poc", "poc_sentinel2_ndvi.csv")):
        path = os.path.join(out_dir, name)
        if os.path.exists(path):
            found[key] = pd.read_csv(path)
    return found
