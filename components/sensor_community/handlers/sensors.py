from src.components import Handler

from src.utilities.geo_json import fetch_geojson_simple


class SensorCommunityHandler(Handler):
    def run(self, start_timestamp: int = None, end_timestamp: int = None):
        return fetch_geojson_simple(
            self.get_table_by_name("sensor_community_sensors"),
            start_timestamp,
            end_timestamp,
        )
