import logging
from datetime import datetime
from datetime import timedelta
from typing import NoReturn

import polars as pl

from gears_testing.api.sheet.spreadsheet import GoogleSheetAPI
from gears_testing.api.strava.strava import StravaAPI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger = logging.getLogger(__name__)

SPREADSHEET_ID = ""  # TODO: add the spreadhseet ID
COLS = [
    'name',
    'distance',
    'moving_time',
    'elapsed_time',
    'total_elevation_gain',
    'start_date_local',
    'id',
    'average_speed',
    'average_cadence'
]


def upload_latest_activities_google_sheet(from_last_n_days: int = 7) -> NoReturn:
    """
    Retrieves the latest activities from Strava and uploads them into a Google spreadsheet
    :param from_last_n_days: timeframe to get the activities from the n last days
    :return:
    """
    st = StravaAPI()
    ts = int(datetime.timestamp(datetime.now() - timedelta(days=from_last_n_days)))
    logger.info("Retrieving data from Strava... [START]")
    latest_activity = st.get_athlete_activities(after=ts)
    logger.info("Retrieving data from Strava.... [DONE]")
    df = pl.from_dicts(latest_activity)

    df = df.with_columns([
        (pl.col('moving_time') / 60).round(2).alias('moving_time'),
        (pl.col('elapsed_time') / 60).round(2).alias('elapsed_time'),
        (pl.col('distance') / 1000).round(2).alias('distance'),
        (pl.col('average_speed') * 3.6).round(2).alias('average_speed'),
        (pl.col('average_cadence') * 2).round(2).alias('average_cadence'),
        (pl.col('max_speed') * 3.6).round(2).alias('max_speed'),
        ]
    )
    ids = df.select('id').to_series().to_list()

    ss = GoogleSheetAPI()
    vals = ss.retrieve_data_from_google_sheet(spreadsheet_id=SPREADSHEET_ID,
                                              rg="G2:G")
    sheets_activities = list(map(lambda x: int(x), sum(vals, [])))
    if to_add := [i for i in ids if i not in sheets_activities]:
        start_from = str(len(sheets_activities) + 2)
        df = df.filter(pl.col('id').is_in(to_add)).select(COLS)
        data_df = [list(r) for r in df.rows()]
        str_data = []
        for d in data_df:
            str_d = list(map(lambda x: str(x).replace('.', ','), d))
            str_data.append(str_d)

        logger.info(f"Adding {len(to_add)} activities... [START]")
        ss.upload_data(spreadsheet_id=SPREADSHEET_ID,
                       data_to_upload=str_data,
                       rg=f"A{start_from}:I"
                       )
        logger.info(f"Adding {len(to_add)} activities.... [DONE]")
    else:
        logger.info('Your activities are up-to-date!')


if __name__ == '__main__':
    upload_latest_activities_google_sheet()
