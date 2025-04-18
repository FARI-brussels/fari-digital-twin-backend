import os
import requests
from src.components import Collector

class TiledPointCloudCollector(Collector):
    def run(self):
        return requests.get("http://localhost:8887/tileset.zip").content