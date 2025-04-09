import requests

from src.components import Collector


class FixMyStreetIncidentsCollector(Collector):
    def run(self):
        data = requests.get(
            "https://fixmystreet.brussels/api/incidents"
        ).json()

        return data
