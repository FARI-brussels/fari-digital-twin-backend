import json
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.components import Collector


class SibelgaSiteCollector(Collector):
    def run(self):
        api_url = "https://www.sibelga.be/fr/chantiers-data/data"
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        if not items:
            return []

        df = pd.DataFrame(items)

        df = df.dropna(subset=["latitude", "longitude"])
        geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]

        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        gdf.drop(columns=["latitude", "longitude"], inplace=True)

        return json.loads(gdf.to_json())
