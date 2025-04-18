from datetime import datetime
from src.components import Handler
from src.data.retrieve import retrieve_before_datetime
import json


class TiledPointCloudHandler(Handler):
    def run(self):
        tilesets = retrieve_before_datetime(
            table=self.get_table_by_name("pointcloud_tilesets"),
            date=datetime.now(),
            limit = 100000,
        )
        return json.dumps([t._url for t in tilesets])
