from datetime import datetime
from src.components import Handler
from src.data.retrieve import retrieve_before_datetime
import json


class WMSHandler(Handler):
    def run(self):
        wms= retrieve_before_datetime(
            table=self.get_table_by_name("wms_wms_layer"),
            date=datetime.now(),
            limit = 100000,
        )
        return [w.data for w in wms]
