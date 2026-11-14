"""Fetch the observed rainfall and greenness record for the parcel.

Needs internet but no login. Usage:  python collect_observations.py
Writes CSV files to data/observed/. Run it once, then commit the files.
"""
from datetime import date

from mrv import observe, pipeline


def main():
    sc = pipeline.load_yaml(pipeline.SCENARIO)
    start = date(2024, 11, 1)                      # start of the proof-of-concept imagery window
    end = date.fromisoformat(sc["timeline"]["as_of"])
    report = observe.collect(pipeline._path(sc["site"]["parcel_geojson"]),
                             pipeline._path("data/observed"), start, end)
    for key, value in report.items():
        print(f"{key:26s} {value}")


if __name__ == "__main__":
    main()
