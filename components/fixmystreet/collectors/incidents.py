import json
import requests
import pandas as pd
import geopandas as gpd
from pyproj import Transformer
from src.components import Collector

class FixMyStreetIncidentsCollector(Collector):
    def run(self):
        # Initialiser le transformateur
        transformer = Transformer.from_crs('EPSG:31370', 'EPSG:4326', always_xy=True)

        # Requête API
        api_url = "https://fixmystreet.brussels/api/incidents"
        response = requests.get(api_url)
        response.raise_for_status()
        response_json = response.json()

        # Extraction des données
        response_df = pd.json_normalize(response_json["_embedded"]["response"])

        # Conversion des coordonnées
        x = response_df["location.coordinates.x"]
        y = response_df["location.coordinates.y"]
        lon, lat = transformer.transform(x.values, y.values)

        # Création des géométries
        geometry = gpd.points_from_xy(lon, lat)
        gdf = gpd.GeoDataFrame(response_df, geometry=geometry, crs="EPSG:4326")

        link_cols = [col for col in gdf.columns if col.startswith('_links.')]

        columns_to_del = [
            'location.coordinates.x',
            'location.coordinates.y',
            *link_cols
        ]

        gdf.drop(columns_to_del, inplace=True, axis=1, errors="ignore")

        # Export GeoJSON
        return json.loads(gdf.to_json())
