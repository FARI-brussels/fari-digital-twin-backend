import os
import requests
from src.components import Collector

class WMSCollector(Collector):
    def run(self):
        try:
            response = requests.get("http://localhost:8887/wms.json")
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.json()
        except requests.exceptions.RequestException:
            return None