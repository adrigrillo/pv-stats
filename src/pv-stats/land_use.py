from pathlib import Path
from typing import List

import geopandas as gpd
import pandas as pd

from config.config import settings
from utils.df_processing import process_land_use_df, join_administrative_divisions_dfs
from utils.io_utils import read_geo_dataframe, save_dataframe


def filter_and_group_land_use_per_id(land_use_df: gpd.GeoDataFrame,
                                     ids: int | List[int]) -> gpd.GeoDataFrame:
    """ Filter the land use by category and group it per city.

    :param land_use_df: land use GeoDataFrame.
    :param ids: id or list of ids from SIOSE with the land use categories to filter.
    :return: filtered and grouped per city GeoDataFrame.
    """
    if isinstance(ids, int):
        ids = [ids]

    filtered_land_use = land_use_df.loc[land_use_df['ID_USO_MAX'].isin(ids)]
    filtered_land_use = filtered_land_use.groupby(
        ['MUNICIPIO', 'MUNICIPIO_NOMBRE'],
        as_index=False
    )['SUPERF_M2'].sum()
    filtered_land_use['superficie_km2'] = filtered_land_use['SUPERF_M2'] / 10 ** 6
    filtered_land_use['superficie_m2'] = filtered_land_use['SUPERF_M2']
    filtered_land_use.drop(columns=['SUPERF_M2'], inplace=True)

    return filtered_land_use


def filter_land_use(land_use_path: str | Path) -> pd.DataFrame:
    """

    :param land_use_path: path to the land use file.
    :return:
    """
    land_use_df = read_geo_dataframe(land_use_path)

    # Filter industrial zones
    industrial_zones_df = filter_and_group_land_use_per_id(land_use_df, settings.land_use.industrial_zones)
    save_dataframe('industrial_zones', industrial_zones_df, saving_folder=settings.results_folder)

    # Filter urban zones
    urban_zones_df = filter_and_group_land_use_per_id(land_use_df, settings.land_use.urban_zones)
    save_dataframe('urban_zones', urban_zones_df, saving_folder=settings.results_folder)

    # Filter service zones
    service_zones_df = filter_and_group_land_use_per_id(land_use_df, settings.land_use.service_zones)
    save_dataframe('service_zones', service_zones_df, saving_folder=settings.results_folder)

    # Filter urbanized zones
    urbanized_zones_df = filter_and_group_land_use_per_id(land_use_df, settings.land_use.urbanized_zones)
    save_dataframe('urbanized_zones', urbanized_zones_df, saving_folder=settings.results_folder)

    # Join all to create a CSV
    merge_industrial = urbanized_zones_df.merge(industrial_zones_df,
                                                how='outer',
                                                on=['MUNICIPIO', 'MUNICIPIO_NOMBRE'],
                                                suffixes=('_urbanized', '_industrial'))
    # This one does not need suffixes because no column name is shared.
    merge_urban = merge_industrial.merge(urban_zones_df,
                                         how='outer',
                                         on=['MUNICIPIO', 'MUNICIPIO_NOMBRE'])
    # This one needs suffixes as previous and new column share name. First urban, then service
    final_df = merge_urban.merge(service_zones_df,
                                 how='outer',
                                 on=['MUNICIPIO', 'MUNICIPIO_NOMBRE'],
                                 suffixes=('_urban', '_service'))

    save_dataframe('superficie_por_municipio', final_df, saving_folder=settings.results_folder)
    return final_df


def calculate_urban_zone_per_city(administrative_divisions_path: str | Path,
                                  land_use: str | Path) -> None:
    administrative_divisions_path = Path(administrative_divisions_path)
    if administrative_divisions_path.exists():
        administrative_divisions_df = read_geo_dataframe(administrative_divisions_path)
    else:
        administrative_divisions_df = join_administrative_divisions_dfs(
            administrative_divisions_path='/data/processed/administrative_divisions.parquet',
            cities_info_path='/data/processed/cities_info.parquet'
        )

    land_use = Path(land_use)
    if land_use.exists():
        land_use_df = gpd.read_file(land_use)
    else:
        land_use_df = process_land_use_df('/data/uso_suelo/28_MADRID.gpkg')

    pass


if __name__ == '__main__':
    land_use_full = '/data/processed/land_use_full.parquet'
    land_use_filtered = '/data/processed/land_use.parquet'
    administrative_divisions = '/data/processed/administrative_divisions_with_info.geojson'

    # calculate_urban_zone_per_city(administrative_divisions, land_use_geo)
    filter_land_use(land_use_full)
