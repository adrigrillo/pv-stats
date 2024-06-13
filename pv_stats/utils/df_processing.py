from pathlib import Path

import geopandas as gpd
import pandas as pd

from pv_stats.config.config import settings
from pv_stats.utils.io_utils import save_geo_dataframe, save_dataframe, read_geo_dataframe, read_dataframe


def merge_geometries(geodataframe: gpd.GeoDataFrame,
                     column_name: str,
                     row_to_keep: str,
                     row_to_remove: str) -> None:
    """ Merge two geometries into one, keeping the data of one row and removing the other.

    :param geodataframe: geopandas dataframe.
    :param column_name: column name to use to locate the rows.
    :param row_to_keep: name of the row to keep.
    :param row_to_remove: name of the row to remove.
    """
    new_row_df = geodataframe[geodataframe[column_name].isin([row_to_keep, row_to_remove])]
    new_row_geom = new_row_df['geometry'].unary_union
    geodataframe.loc[geodataframe[column_name] == row_to_keep, 'geometry'] = new_row_geom
    geodataframe.drop(geodataframe[geodataframe[column_name] == row_to_remove].index, inplace=True)


def process_administrative_divisions_df(administrative_divisions_path: str | Path) -> gpd.GeoDataFrame:
    """ Process administrative divisions data to convert to numbers and set a common index.

    :param administrative_divisions_path: path to the administrative divisions file.
    :return: GeoDataFrame with the administrative divisions.
    """
    administrative_divisions_path = Path(administrative_divisions_path)
    administrative_divisions_df = gpd.read_file(administrative_divisions_path, layer='IDEM_CM_UNID_ADMIN')

    # Convert to numbers, CD_MUNICIPIO is the most important as it will be used as key
    administrative_divisions_df['CD_NATCODE'] = pd.to_numeric(administrative_divisions_df['CD_NATCODE'],
                                                              downcast='integer')
    administrative_divisions_df['CDID'] = pd.to_numeric(administrative_divisions_df['CDID'],
                                                        downcast='integer')
    administrative_divisions_df['CD_MUNICIPIO'] = pd.to_numeric(administrative_divisions_df['CD_MUNICIPIO'],
                                                                downcast='integer')
    administrative_divisions_df['CD_INE'] = pd.to_numeric(administrative_divisions_df['CD_INE'],
                                                          downcast='integer')
    administrative_divisions_df['CD_INE_1'] = pd.to_numeric(administrative_divisions_df['CD_INE_1'],
                                                            downcast='integer')

    # El Redegüelo belongs to El Boalo
    merge_geometries(administrative_divisions_df,
                     column_name='DS_NOMBRE',
                     row_to_keep='El Boalo',
                     row_to_remove='El Redegüelo')
    # Los Baldios belongs to Navacerrada
    merge_geometries(administrative_divisions_df,
                     column_name='DS_NOMBRE',
                     row_to_keep='Navacerrada',
                     row_to_remove='Los Baldios')

    # Calculate the square meters
    administrative_divisions_df['superficie_km2'] = administrative_divisions_df['geometry'].area / 10 ** 6

    # Save
    save_geo_dataframe('administrative_divisions', administrative_divisions_df)
    return administrative_divisions_df


def process_cities_info_df(cities_info_path: str | Path) -> pd.DataFrame:
    """ Process administrative divisions data to convert to numbers, sanitize the names and
    set a common index.

    :param cities_info_path: path to the administrative divisions file.
    :return: GeoDataFrame with the administrative divisions.
    """
    cities_info_path = Path(cities_info_path)
    cities_info_df = pd.read_csv(cities_info_path,
                                 sep=';', encoding='ISO-8859-1')

    # Convert to numbers, CD_MUNICIPIO is the most important as it will be used as key
    cities_info_df['municipio_codigo'] = pd.to_numeric(cities_info_df['municipio_codigo'],
                                                       downcast='integer')
    cities_info_df['municipio_codigo_ine'] = pd.to_numeric(cities_info_df['municipio_codigo_ine'],
                                                           downcast='integer')
    cities_info_df['nuts4_codigo'] = pd.to_numeric(cities_info_df['nuts4_codigo'],
                                                   downcast='integer')
    cities_info_df['superficie_km2'] = pd.to_numeric(cities_info_df['superficie_km2'])
    cities_info_df['densidad_por_km2'] = pd.to_numeric(cities_info_df['densidad_por_km2'])

    # Sanitize names
    cities_info_df['municipio_nombre'] = cities_info_df['municipio_nombre'].str.strip()

    # Estimate the population
    cities_info_df['population'] = cities_info_df['superficie_km2'] * cities_info_df['densidad_por_km2']
    cities_info_df['population'] = cities_info_df['population'].round().astype(int)

    # Save
    save_dataframe('cities_info', cities_info_df)
    return cities_info_df


def process_consumption_per_city_df(consumption_per_city_path: str | Path) -> pd.DataFrame:
    """ Process consumption per city data to convert to numbers and sanitize the names.

    :param consumption_per_city_path:
    :return:
    """
    consumption_per_city_path = Path(consumption_per_city_path)
    consumption_per_city_df = pd.read_csv(consumption_per_city_path, encoding='ISO-8859-1')

    # Sanitize names
    consumption_per_city_df['Nombre'] = consumption_per_city_df['Nombre'].str.strip()

    # Remove points from the MWh columns, so they can be converted to numeric
    consumption_per_city_df.iloc[:, 1:] = consumption_per_city_df.iloc[:, 1:].map(lambda x: x.replace('.', ''))
    consumption_per_city_df.iloc[:, 1:] = consumption_per_city_df.iloc[:, 1:].apply(pd.to_numeric,
                                                                                    args=('coerce', 'integer'))

    # Save
    save_dataframe('consumption_per_city', consumption_per_city_df)
    return consumption_per_city_df


def process_urban_zones_df(urban_zones_path: str | Path) -> gpd.GeoDataFrame:
    """ Process urban zones data to a UTM projection and calculate the area in m2.

    :param urban_zones_path: path to the urban zones file.
    :return: processed GeoDataFrame.
    """
    urban_zones_path = Path(urban_zones_path)
    urban_zones_df = gpd.read_file(urban_zones_path)

    # Move to UTM zone 30, to calculate the areas
    urban_zones_df.to_crs('EPSG:23030', inplace=True)

    # Add the area of the polygons in m2
    urban_zones_df['superficie_m2'] = urban_zones_df['geometry'].area

    # Save
    save_geo_dataframe('urban_zones', urban_zones_df)
    return urban_zones_df


def process_land_use_df(land_use_path: str | Path) -> gpd.GeoDataFrame:
    """ Process land use data to filter those urban zones and calculate the area in m2.

    :param land_use_path: path to the land use file.
    :return: filtered GeoDataFrame.
    """
    land_use_path = Path(land_use_path)
    land_use_df = gpd.read_file(land_use_path, layer='SAR_28_T_USOS')
    land_use_df = land_use_df.loc[land_use_df['ID_USO_MAX'].isin(settings.land_use.urban_zones)]

    # Save
    save_geo_dataframe('land_use', land_use_df)
    return land_use_df


def join_administrative_divisions_dfs(administrative_divisions_path: str | Path,
                                      cities_info_path: str | Path) -> gpd.GeoDataFrame:
    """

    :param administrative_divisions_path:
    :param cities_info_path:
    :return:
    """
    administrative_divisions_path = Path(administrative_divisions_path)
    if administrative_divisions_path.exists():
        administrative_divisions_df = read_geo_dataframe(administrative_divisions_path)
    else:
        administrative_divisions_df = process_administrative_divisions_df('/data/DIVISIONES_ADMINISTRATIVAS_CM.gpkg')

    cities_info_path = Path(cities_info_path)
    if cities_info_path.exists():
        administrative_divisions_info_df = read_dataframe(cities_info_path)
    else:
        administrative_divisions_info_df = process_cities_info_df('/data/cities_info.csv')

    # Match city per administrative division
    cities_info_geo = administrative_divisions_df.merge(administrative_divisions_info_df,
                                                        left_on='CD_MUNICIPIO',
                                                        right_on='municipio_codigo')

    # Remove redundant columns
    cities_info_geo.drop(['CD_MUNICIPIO', 'CD_INE_1', 'superficie_km2_x'], axis=1, inplace=True)
    cities_info_geo['superficie_km2'] = cities_info_geo['superficie_km2_y']
    cities_info_geo.drop(['superficie_km2_y'], axis=1, inplace=True)

    # Reorder columns
    cities_info_geo = cities_info_geo[['municipio_codigo',
                                       'municipio_nombre',
                                       'DS_NOMBRE',
                                       'DS_DESCRIPCION',
                                       'municipio_codigo_ine',
                                       'CD_INE',
                                       'nuts4_codigo',
                                       'nuts4_nombre',
                                       'CDID',
                                       'CD_NATCODE',
                                       'superficie_km2',
                                       'densidad_por_km2',
                                       'population',
                                       'geometry']]

    save_geo_dataframe('administrative_divisions_with_info', cities_info_geo)
    return cities_info_geo


def remap_column_categories(gdf_path: str | Path,
                            column_name: str,
                            categories_mapping: dict[str, str],
                            saving_path: str | Path = None) -> gpd.GeoDataFrame:
    """
    Transform the categories of a GeoDataFrame column.

    :param gdf_path: path to the GeoDataFrame.
    :param column_name: column with the land use categories.
    :param categories_mapping: dictionary with the land use categories to be transformed.
    :param saving_path: path to save the transformed GeoDataFrame.
    :return: GeoDataFrame with the transformed land use categories.
    """
    gdf = gpd.read_file(gdf_path)
    gdf[column_name] = gdf[column_name].map(categories_mapping)
    if saving_path:
        gdf.to_file(saving_path)
    return gdf


if __name__ == '__main__':
    # process_administrative_divisions_df('/data/DIVISIONES_ADMINISTRATIVAS_CM.gpkg')
    # process_cities_info_df('/data/municipio_comunidad_madrid.csv')
    # process_consumption_per_city_df('/data/electricidad_municipios.csv')
    # process_urban_zones_df('/data/uso_suelo/elucm_ExistingLandUseDataObject.gpkg')
    process_land_use_df('/data/uso_suelo/28_MADRID.gpkg')
    #
    # join_administrative_divisions_dfs('/data/processed/administrative_divisions.parquet',
    #                                   '/data/processed/cities_info.parquet')
