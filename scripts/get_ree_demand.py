import os
from pathlib import Path
from typing import Optional, Annotated

import pandas as pd
import typer
from dateutil.parser import isoparse
from loguru import logger
from pandas import DataFrame

from pv_stats.ree.ree_api import REEDataAPI, throttle_request_dates


def retrieve_demand_data(
        save_path: Annotated[str, typer.Argument(help='Path to a folder where the data will be saved or '
                                                      'full path to the file.')],
        start_date: Annotated[str, typer.Argument(help='Start date to retrieve the data in ISO 8601 format.')],
        end_date: Annotated[str, typer.Argument(help='End date to retrieve the data in ISO 8601 format.')],
        time_trunc: Annotated[Optional[str], typer.Argument(help='Defines the time aggregation '
                                                                 'of the requested data.')] = 'hour'
) -> None:
    ree_api = REEDataAPI()
    logger.info('Retrieving demand data from REE API from {} to {}.', start_date, end_date)

    # Check the dates to throttle the request, it cannot retrieve long periods
    request_dates = throttle_request_dates(start_date, end_date)
    # Generate the dataframe and add the data to it
    demand_dfs = list()
    for start_day, end_day in request_dates:
        data = ree_api.get_demand(
            start_date=start_day,
            end_date=end_day,
            time_trunc=time_trunc,
            geo_trunc=None,
            geo_limit=None,
            geo_ids=None
        )

        demand_dfs.append(data)

    demand_df = pd.concat(demand_dfs)

    save_path = Path(save_path)
    if save_path.is_dir():
        start_str = isoparse(start_date).strftime('%Y%m%d')
        end_str = isoparse(end_date).strftime('%Y%m%d')
        save_path = save_path / f'ree_demand_{start_str}_{end_str}.csv'

    os.makedirs(save_path.parent, exist_ok=True)
    demand_df.to_csv(save_path)


if __name__ == '__main__':
    typer.run(retrieve_demand_data)
