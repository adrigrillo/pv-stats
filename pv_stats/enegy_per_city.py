from pathlib import Path

import geopandas as gpd

from pv_stats.utils.df_processing import (process_administrative_divisions_df,
                                          process_cities_info_df,
                                          process_consumption_per_city_df)


def draw_consumption_per_city(cities_info: str | Path,
                              consumption_per_city: str | Path,
                              administrative_divisions: str | Path) -> None:
    """

    :param cities_info:
    :param administrative_divisions:
    :param consumption_per_city:
    :return:
    """
    cities_info_df = process_cities_info_df(cities_info)
    consumption_per_city_df = process_consumption_per_city_df(consumption_per_city)

    administrative_divisions_df = process_administrative_divisions_df(administrative_divisions)

    # Match city per administrative division
    cities_info_geo = cities_info_df.merge(administrative_divisions_df,
                                           left_index=True, right_index=True)
    # Match city with consumption
    cities_info_and_consumption_df = cities_info_geo.merge(consumption_per_city_df,
                                                           left_on='municipio_nombre',
                                                           right_on='Nombre')

    # Calculate interesting things
    cities_info_and_consumption_df['consumption_per_capita'] = (cities_info_and_consumption_df['2021'] /
                                                                cities_info_and_consumption_df['population'])
    cities_info_and_consumption_df['consumption_per_km2'] = (cities_info_and_consumption_df['2021'] /
                                                             cities_info_and_consumption_df['superficie_km2'])

    cities_info_and_consumption_geo = gpd.GeoDataFrame(cities_info_and_consumption_df, geometry='geometry')
    cities_info_and_consumption_geo.to_file('/data/cities_info_and_consumption.geojson', driver='GeoJSON')


if __name__ == '__main__':
    cities_data = '/data/municipio_comunidad_madrid.csv'
    elec_per_city = '/data/electricidad_municipios.csv'
    ad_divisions = '/data/DIVISIONES_ADMINISTRATIVAS_CM.gpkg'

    draw_consumption_per_city(cities_data, elec_per_city, ad_divisions)
