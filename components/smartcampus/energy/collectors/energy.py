from src.components import Collector
import requests


class EnergyCollector(Collector):
    def run(self) -> dict:
        response = requests.get(
            "http://api.el.sc.ulb.be/energy"
        )

        return response.json()
