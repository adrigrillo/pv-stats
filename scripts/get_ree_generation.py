import os
from pathlib import Path
from typing import Optional, Annotated

import pandas as pd
import typer
from dateutil.parser import isoparse
from loguru import logger

from pv_stats.ree.ree_api import REEDataAPI
from pv_stats.ree.ree_demanda_api import REEDemandaAPI


def retrieve_demand_data(
        save_path: Annotated[
            str,
            typer.Argument(help='Path to a folder where the data will be saved or full path to the file.')
        ],
        start_date: Annotated[
            str,
            typer.Argument(help='Start date to retrieve the data in ISO 8601 format.')
        ],
        end_date: Annotated[
            Optional[str],
            typer.Argument(help='End date to retrieve the data in ISO 8601 format.')
        ] = None,
        time_trunc: Annotated[
            Optional[str],
            typer.Argument(help='Defines the time aggregation to retrieve the data.')
        ] = 'hour',
        geo_limit: Annotated[
            Optional[str],
            typer.Argument(help='Defines the zone to retrieve the data.')
        ] = None
) -> None:
    if end_date is None:
        end_date = start_date

    # Get all the dates between the start and end date
    logger.info('Retrieving demand data from REE demand API from {} to {}.', start_date, end_date)

    if time_trunc == 'hour':
        ree_api = REEDemandaAPI()
        if geo_limit is None:
            geo_limit = 'NACIONAL'
        # This API requires to retrieve the data day by day
        dates = pd.date_range(start_date, end_date, freq='D')

        # Generate the dataframe and add the data to it
        demand_dfs = list()
        for date in dates:
            data = ree_api.get_generation(
                date=date,
                geo_limit=geo_limit
            )

            demand_dfs.append(data)

        demand_df = pd.concat(demand_dfs)
    else:
        ree_api = REEDataAPI()
        # Check the dates to throttle the request, it cannot retrieve long periods
        # Generate the dataframe and add the data to it
        demand_df = ree_api.get_generation_estructure(
            start_date=start_date,
            end_date=end_date,
            time_trunc=time_trunc,
            geo_trunc=None,
            geo_limit=geo_limit,
            geo_ids=None,
        )

    save_path = Path(save_path)
    if save_path.is_dir():
        start_str = isoparse(start_date).strftime('%Y%m%d')
        end_str = isoparse(end_date).strftime('%Y%m%d')
        save_path = save_path / f'ree_generation_{time_trunc}_{start_str}_{end_str}.csv'

    os.makedirs(save_path.parent, exist_ok=True)
    demand_df.to_csv(save_path)


if __name__ == '__main__':
    typer.run(retrieve_demand_data)
