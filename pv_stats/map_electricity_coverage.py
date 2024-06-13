from pathlib import Path

import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt

from pv_stats.config.config import settings
from pv_stats.utils.io_utils import read_dataframe, read_geo_dataframe


def process_fv_coverage(file_path: str | Path) -> gpd.GeoDataFrame:
    """
    Process the excel file with the cities data to get the electricity coverage.

    :param file_path: The path to the excel file.
    :return: None
    """
    df = read_dataframe(file_path)

    # En este dataset hay columnas que se sacan con cálculos, como la potencia en cubierta.
    # Vamos a recrearlas aquí, usando las columnas con datos y ciertos parámetros.
    # Cogemos de las columnas A:F, que son las que tienen datos definidos.
    df = df.iloc[:, :6]
    column_rename = settings.pv_coverage.column_rename
    df.rename(columns=column_rename, inplace=True)

    # Creamos una nueva columna con la potencia en cubierta en MW, que es la potencia que se puede instalar
    # en la superficie urbana. Requiere del parámetro potencia por hectárea.
    power_per_ha_roof = settings.pv_coverage.power_per_ha_roof
    df['power_in_roof'] = df['urban_ha'] * power_per_ha_roof / 1000

    # Creamos otra columna con la demanda de electricidad anual cubierta en MWh por lo
    # instalado en cubiertas. Requiera las horas estimadas de funcionamiento al año.
    hef_roof = settings.pv_coverage.hef_roof
    # Create a temporal column that is the anual electricity generated in MWh using the power in roof and the hef
    df['electricity_generated_annually'] = df['power_in_roof'] * hef_roof
    # Then take the minimum between the electricity covered and the demand
    df['electricity_covered_annually'] = df[
        [
            'electricity_generated_annually',
            'mean_electricity_consumption'
        ]
    ].min(axis=1)

    # Sacamos el porcentaje de la demanda cubierta
    df['covered_percentage'] = df['electricity_covered_annually'] / df['mean_electricity_consumption']

    # Vamos a sacar los datos para un porcentaje de demanda cubierta
    consumption_to_cover = settings.pv_coverage.consumption_to_cover
    # Sacamos la cantidad de MWh que se necesitaría instalar en suelo para cubrir la demanda, quitando
    # lo que ya se cubre con las cubiertas.
    # La fórmula en excel es =IF(covered_percentage<consumption_to_cover;
    # (consumption_to_cover*mean_electricity_consumption-electricity_covered_annually); 0)
    df['electricity_required_in_floor'] = df.apply(
        lambda x: (
                consumption_to_cover *
                x['mean_electricity_consumption'] -
                x['electricity_covered_annually']
        ) if x['covered_percentage'] < consumption_to_cover else 0,
        axis=1
    )

    # La potencia en suelo necesaria para cubrir la demanda.
    hef_floor = settings.pv_coverage.hef_floor
    df['power_in_floor'] = df['electricity_required_in_floor'] / hef_floor

    # La superficie en suelo necesaria para conseguir dicha potencia.
    power_per_ha_flor = settings.pv_coverage.power_per_ha_floor
    # Pasar de kW a MW
    df['floor_ha'] = df['power_in_floor'] / (power_per_ha_flor / 1000)

    # Superficie rural que se usaría para instalar la potencia en suelo.
    df['used_rural_floor'] = df['floor_ha'] / df['rural_ha']

    return df


def relate_fv_location_df(df: pd.DataFrame, geo_df: str | Path) -> gpd.GeoDataFrame | pd.DataFrame:
    """
    Relate the electricity coverage data with the localization data.

    :param df: pd.DataFrame: The electricity coverage data.
    :param geo_df: gpd.GeoDataFrame: The localization data.
    :return: gpd.GeoDataFrame
    """
    geo_df = read_geo_dataframe(geo_df)
    df['municipio'] = df['municipio'].str.strip()
    # Join the dataframes by the 'municipio_nombre' column in the geo_df and the
    # 'municipio' column in the df
    join_df = geo_df.merge(df, left_on='municipio_nombre', right_on='municipio')

    return join_df


def plot_geo_fv_coverage(geo_fv_coverage_df: gpd.GeoDataFrame,
                         save_path: str | Path) -> None:
    """
    Plots the percentage of coverage that can be achieved with the data extracted
    per city, whose limits are defined in the geometry column.

    :param geo_fv_coverage_df: photovoltaic coverage data per city.
    :param save_path: path to save the plot.
    """
    # The coverage percentage goes from 0 to 1, where 0 is that no demand is covered
    # and 1 is that all the demand is covered. We will group in 5 categories.
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1]
    labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    geo_fv_coverage_df['coverage_category'] = pd.cut(geo_fv_coverage_df['covered_percentage'],
                                                     bins=bins,
                                                     labels=labels)

    # Plot the data
    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    geo_fv_coverage_df.plot(column='coverage_category',
                            ax=ax,
                            edgecolor='black',
                            legend=True,
                            legend_kwds={'loc': 'upper left',
                                         'fontsize': 25},
                            cmap='summer_r')

    consumption_to_cover = settings.pv_coverage.consumption_to_cover * 100
    ax.set_title(f'Porcentaje de demanda eléctrica cubierto por paneles fotovoltaicos\n'
                 f'en cubiertas sobre el {consumption_to_cover}% de la demanda total de cada municipio',
                 fontsize=30)
    ax.set_axis_off()
    plt.savefig(save_path)
    plt.show()
    plt.close()


def plot_rural_floor_ha_required(geo_fv_coverage_df: gpd.GeoDataFrame,
                                 save_path: str | Path) -> None:
    """
    Plots the percentage over the rural floor required to cover the demand established
    per city, whose limits are defined in the geometry column.

    :param geo_fv_coverage_df: photovoltaic coverage data per city.
    :param save_path: path to save the plot.
    """
    # Plot the data
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    geo_fv_coverage_df.plot(column='used_rural_floor',
                            ax=ax,
                            edgecolor='black',
                            legend=True,
                            legend_kwds={'location': 'bottom',
                                         'orientation': 'horizontal',
                                         'pad': 0,
                                         'shrink': 0.75},
                            cmap='summer_r')

    consumption_to_cover = settings.pv_coverage.consumption_to_cover * 100
    ax.set_title(f'Porcentaje del suelo rural requerido para llegar a cubrir\n'
                 f'el {consumption_to_cover}% de la demanda eléctrica en cada municipio')

    ax.set_axis_off()
    plt.savefig(save_path)
    plt.show()
    plt.close()


if __name__ == '__main__':
    fv_coverage_path = '/data/resumen_fv_municipios.csv'
    administrative_divisions_path = '/data/processed/administrative_divisions_with_info.geojson'
    fv_coverage_df = process_fv_coverage(fv_coverage_path)
    fv_coverage_geo_df = relate_fv_location_df(fv_coverage_df, administrative_divisions_path)
    fv_coverage_geo_df.to_file('/data/results/fv_coverage.geojson', driver='GeoJSON')
    # plot_geo_fv_coverage(fv_coverage_geo_df, '/data/results/fv_coverage.png')
    plot_rural_floor_ha_required(fv_coverage_geo_df, '/data/results/fv_coverage_rural.png')
