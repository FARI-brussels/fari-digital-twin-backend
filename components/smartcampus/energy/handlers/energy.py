from src.components import Handler
from src.data.retrieve import retrieve_first_row
import json


class EnergyHandler(Handler):
    def run(self):
        datas = retrieve_first_row(self.get_table_by_name("energy_sensors"))

        if not datas:
            return {"error": "No data found"}

        data_str = datas.data.decode('utf-8')

        return json.loads(data_str)
