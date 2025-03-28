import json
import geopandas as gpd
import pandas as pd
import requests

from src.components import Collector

class SensorCommunityCollector(Collector):
    def run(self):
        api_url = "https://data.sensor.community/airrohr/v1/filter/area=50.8503,4.3517,10"
        response = requests.get(api_url)
        response.raise_for_status()
        response_json = response.json()

        response_df = pd.json_normalize(response_json, max_level=4)

        geometry = gpd.points_from_xy(
            response_df['location.longitude'],
            response_df['location.latitude']
        )

        gdf = gpd.GeoDataFrame(response_df, geometry=geometry, crs="EPSG:4326")

        columns_to_remove = [
            'location.exact',
            'location.altitude',
            'sensor.pin',
            'sensor.sensor_type.id',
            'location.country',
            'sampling_rate',
        ]

        gdf.drop(columns=columns_to_remove, axis=1, inplace=True, errors='ignore')

        return json.loads(gdf.to_json())
