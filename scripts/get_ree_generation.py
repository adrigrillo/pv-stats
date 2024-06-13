import os
from pathlib import Path
from time import sleep
from typing import Optional, Annotated

import pandas as pd
import typer
from dateutil.parser import isoparse
from loguru import logger

from pv_stats.ree.ree_demanda_api import REEDemandaAPI


def retrieve_demand_data(
        save_path: Annotated[str, typer.Argument(help='Path to a folder where the data will be saved or '
                                                      'full path to the file.')],
        start_date: Annotated[str, typer.Argument(help='Start date to retrieve the data in ISO 8601 format.')],
        end_date: Annotated[str, typer.Argument(help='End date to retrieve the data in ISO 8601 format.')],
        geo_limit: Annotated[Optional[str], typer.Argument(help='Defines the zone to retrieve the data.')] = 'NACIONAL'
) -> None:
    ree_api = REEDemandaAPI()
    logger.info('Retrieving demand data from REE demand API from {} to {}.', start_date, end_date)

    # Get all the dates between the dates
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

    save_path = Path(save_path)
    if save_path.is_dir():
        start_str = isoparse(start_date).strftime('%Y%m%d')
        end_str = isoparse(end_date).strftime('%Y%m%d')
        save_path = save_path / f'ree_generation_{start_str}_{end_str}.csv'

    os.makedirs(save_path.parent, exist_ok=True)
    demand_df.to_csv(save_path)


if __name__ == '__main__':
    typer.run(retrieve_demand_data)
