import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger

from pv_stats.config.config import settings


def read_geo_dataframe(path_to_df: str | Path,
                       layer: str = None) -> gpd.GeoDataFrame:
    """
    Read a GeoDataFrame from a specified path.

    :param path_to_df: The path to the GeoDataFrame.
    :param layer: name of the layer to read.
    :return: gpd.GeoDataFrame
    """
    path_to_df = Path(path_to_df)
    if path_to_df.suffix == '.parquet':
        df = gpd.read_parquet(path_to_df)
    elif path_to_df.suffix == '.gpkg':
        if not layer:
            logger.warning('Layer not specified.')
        df = gpd.read_file(path_to_df, layer=layer)
    else:
        df = gpd.read_file(path_to_df)

    return df


def save_geo_dataframe(name: str,
                       geo_df: gpd.GeoDataFrame,
                       saving_folder: str = settings.processed_data_folder) -> None:
    """
    Save the given GeoDataFrame to a file with the specified name and format.

    :param name: str: The name of the file to save.
    :param geo_df: gpd.GeoDataFrame: The GeoDataFrame to save.
    :param saving_folder: path to the folder where to save the GeoDataFrame.
    :return: None
    """
    os.makedirs(saving_folder, exist_ok=True)
    saving_format = settings.geodata.saving_format
    if saving_format == 'parquet':
        geo_df.to_parquet(f'{saving_folder}/{name}.{saving_format}')
    else:
        geo_df.to_file(f'{saving_folder}/{name}.{saving_format}')


def read_dataframe(path_to_df: str | Path,
                   sheet_name: str = None) -> pd.DataFrame:
    """
    Read a dataframe from a specified path.

    :param path_to_df: The path to the dataframe.
    :return: pd.DataFrame
    """
    path_to_df = Path(path_to_df)
    if path_to_df.suffix == '.parquet':
        df = pd.read_parquet(path_to_df)
    elif path_to_df.suffix == '.csv':
        df = pd.read_csv(path_to_df)
    elif path_to_df.suffix == '.json':
        df = pd.read_json(path_to_df)
    elif path_to_df.suffix == '.xlsx':
        xl = pd.ExcelFile(path_to_df)
        if not sheet_name:
            logger.warning('Sheet name not specified.')
        df = xl.parse(sheet_name)
    else:
        raise NotImplementedError('The file format is not supported yet.')

    return df


def save_dataframe(name: str,
                   df: pd.DataFrame,
                   saving_folder: str = settings.processed_data_folder) -> None:
    """
    Saves the dataframe to a specified folder in the desired format.

    :param name: str: The name of the dataframe.
    :param df: pd.DataFrame: The dataframe to be saved.
    :param saving_folder: path to the folder where to save the dataframe.
    :return: None
    """
    os.makedirs(saving_folder, exist_ok=True)
    saving_format = settings.data.saving_format
    if saving_format == 'parquet':
        df.to_parquet(f'{saving_folder}/{name}.{saving_format}')
    elif saving_format == 'csv':
        df.to_csv(f'{saving_folder}/{name}.{saving_format}')
    elif saving_format == 'json':
        df.to_json(f'{saving_folder}/{name}.{saving_format}')
    else:
        raise NotImplementedError('The saving format is not supported yet.')
