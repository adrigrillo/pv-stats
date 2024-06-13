from pv_stats.utils.df_processing import remap_column_categories

if __name__ == '__main__':
    land_use_equivalence = {
        "URB1": "URB-SUR",
        "URB2": "URB-SE-SO",
        "URB3": "URB-E-O",
        "URB4": "URB-PLANA",
        "URB5": "URB-INFR",
        "IND1": "IND-SUR",
        # No están definidos en el nuevo esquema, tampoco hay nada etiquetado
        # "IND2": "IND-",
        # "IND3": "IND-",
        # "IND4": "IND-",
        "IND5": "IND-NORTE",
        "EXT": "EXT"
    }

    remap_column_categories(
        gdf_path='/data/poligonos/zonas Rodrigo/capa_superficie_utilizable.shp',
        column_name='categoria',
        categories_mapping=land_use_equivalence,
        saving_path='/data/poligonos/zonas Rodrigo/capa_superficie_utilizable_nuevo_esquema.shp'
    )
