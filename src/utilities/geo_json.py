from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from geopandas import GeoDataFrame
from sqlalchemy import Table

from src.data.retrieve import retrieve_between_datetime


def fetch_geojson_simple(
    table: Table,
    start_timestamp: int = None,
    end_timestamp: int = None,
    columns_to_drop: list = None,
):
    local_tz = ZoneInfo("Europe/Brussels")
    now = datetime.now(local_tz)

    start = (
        datetime.fromtimestamp(start_timestamp, local_tz)
        if start_timestamp is not None
        else now - timedelta(hours=1)
    )
    end = (
        datetime.fromtimestamp(end_timestamp, local_tz)
        if end_timestamp is not None
        else now
    )

    datas = retrieve_between_datetime(table, start, end, limit=2000)
    if not datas:
        return {"features": [], "type": "FeatureCollection"}

    df = GeoDataFrame()

    for item in datas:
        gdf = GeoDataFrame.from_features(item.data["features"])
        gdf["datetimes"] = item.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        df = pd.concat([df, gdf])

    if columns_to_drop:
        df.drop(columns=columns_to_drop, inplace=True)

    return df.__geo_interface__