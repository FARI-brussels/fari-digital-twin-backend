import os
import requests
from src.components import Collector

class TiledPointCloudCollector(Collector):
    def run(self):
        try:
            response = requests.get("http://localhost:8887/tileset.zip")
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.content
        except requests.exceptions.RequestException:
            return None