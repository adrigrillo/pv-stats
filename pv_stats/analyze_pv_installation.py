from pathlib import Path

import pandas as pd
from loguru import logger

from pv_stats.utils.df_processing import remap_column_categories
from pv_stats.utils.io_utils import read_geo_dataframe


def analyze_pv_installation(pv_paths: list[str | Path],
                            categories_mapping: dict[str, str],
                            save_path: str | Path) -> None:
    # Create an empty geodataframe and then join all the pv installations
    global_gdf = None
    for pv_path in pv_paths:
        gdf = read_geo_dataframe(pv_path)
        gdf['area_m2'] = gdf['geometry'].area
        if global_gdf is None:
            global_gdf = gdf
        else:
            global_gdf = pd.concat([global_gdf, gdf], ignore_index=True)

    global_gdf.to_file(save_path, driver='GeoJSON')

    # Select the polygons inside each of the 'EXT' rows in the 'categoria' column
    global_gdf['categoria'] = global_gdf['categoria'].map(categories_mapping)
    ext_gdf = global_gdf[global_gdf['categoria'] == 'Perimetro']
    for index, row in ext_gdf.iterrows():
        elements_inside = global_gdf[global_gdf['geometry'].within(row['geometry'])]
        # Group by the 'categoria' column and sum the 'area_m2' column
        categories_area = elements_inside.groupby('categoria')['area_m2'].sum()
        # Retrieve the categories that are not 'Perimetro' and check the string of each of them,
        # taking the substring from the beginning to the first '-' character
        categories = categories_area.index[categories_area.index != 'Perimetro']
        land_type = None
        for category in categories:
            local_land_type = category.split('-')[0].strip()
            if land_type is None:
                land_type = local_land_type
            elif land_type != local_land_type:
                logger.warning(f'Land type mismatch: {land_type} != {local_land_type}')

        logger.info('El périmetro es de tipo {}', land_type)
        categories_area = categories_area / 10000

        # Print a table with the categories and the area of each of them, rounded to int
        logger.info(categories_area.round().astype(int))





if __name__ == '__main__':
    pv_files = [
        '/data/poligonos/poligono alcorcón/polígono-alcorcon.shp',
        '/data/poligonos/zonas Rodrigo/capa_superficie_utilizable_nuevo_esquema.shp'
    ]
    categories_map = {
        "EXT": "Perimetro",
        "IND-SUR": "Industrial - S (≤89°) inclinacion cubierta",
        "IND-NORTE": "Industrial - N (90°) inclinacion cubierta",
        "IND-NOR2": "Industrial - N (90°) inclinacion sur 5°",
        "IND-PLANA": "Industrial - S/E/O/SE/SO Cubierta plana",
        "IND-SUELO": "Industrial - S/E/O/SE/SO en suelo",
        "IND-INFR": "Industrial - SE/S/SO en pérgola",
        "URB-SUR": "Urbano - S (≤45°) inclinaciéon cubierta",
        "URB-SE-SO": "Urbano - SE/SO (+75 a +45°) inclinacion cubierta",
        "URB-E-O": "Urbano - E/O (≤90 a +45°) inclinacién cubierta",
        "URB-PLANA": "Urbano - S/E/O/SE/SO Cubierta plana",
        "URB-SUELO": "Urbano - S/E/O/SE/SO en suelo",
        "URB-INFR": "Urbano - S/E/O/SE/SO en pérgola"
    }
    saving_path = '/data/poligonos/pv_installations.geojson'
    analyze_pv_installation(pv_files, categories_map, saving_path)

