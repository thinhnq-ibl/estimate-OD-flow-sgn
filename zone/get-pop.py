import pandas as pd
import rasterio.mask
import rasterio.features
import geopandas as gpd
import numpy as np
from shapely.geometry import box
from get_shape_city import get_geometry
from shapely.ops import unary_union
import osmnx as ox

tif_file = "../map/sgp_pop_2025_CN_1km_R2025A_UA_v1.tif"
output_geojson = "pop_grid.geojson"

pois_gdf = gpd.read_file("../zone/detail_pois.geojson")

for index, row in pois_gdf.iterrows():
    print(row['SUBZONE_C'])
    # get population count for this zone
    geometry = row['geometry']
    with rasterio.open(tif_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, [geometry], crop=True)
        out_image = out_image[0]  # Assuming single band
        pop_count = np.sum(out_image[out_image > 0])  # Sum only positive values
        pois_gdf.at[index, 'population'] = pop_count

pois_gdf.to_file(output_geojson, driver='GeoJSON')
print("Done! Detailed counts saved.")