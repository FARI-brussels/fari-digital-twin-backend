import json
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.components import Collector


class OpenSkyCollector(Collector):
    def run(self):
        api_url = (
            "https://opensky-network.org/api/states/all"
            "?lamin=50.775029&lomin=4.193481&lamax=50.962233&lomax=4.578003"
        )

        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        states = data.get("states", [])

        if not states:
            return []

        columns = [
            "icao24", "callsign", "origin_country", "time_position", "last_contact",
            "longitude", "latitude", "baro_altitude", "on_ground", "velocity", "heading",
            "vertical_rate", "sensors", "geo_altitude", "squawk", "spi", "position_source"
        ]

        df = pd.DataFrame(states, columns=columns)
        df = df.dropna(subset=["latitude", "longitude"])

        geometry = [
            Point(lon, lat, alt)
            for lon, lat, alt in zip(
                df["longitude"], df["latitude"], df["geo_altitude"].fillna(0)
            )
        ]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        gdf.drop(columns=["longitude", "latitude", "geo_altitude"], inplace=True)

        return json.loads(gdf.to_json())
