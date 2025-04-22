import os
import requests
from src.components import Collector

class TiledBimCollector(Collector):
    def run(self):
        return requests.get("http://localhost:8887/tileset.zip").content