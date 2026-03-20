import rasterio
import rasterio.mask
import geopandas as gpd
import numpy as np
from shapely.geometry import box
from get_shape_city import get_geometry2

tif_file = "../map/sgp_pop_2025_CN_1km_R2025A_UA_v1.tif"
output_geojson = "city_grid.geojson"

with rasterio.open(tif_file) as src:
    print(src.crs)
    seoul_gdf = get_geometry2()
    
    # 1. Mask and Crop
    out_image, out_transform = rasterio.mask.mask(src, seoul_gdf.geometry, crop=True, filled=False)
    
    data = out_image[0]
    pixel_mask = np.ma.getmaskarray(data)
    
    geometries, pop_values, global_ids = [], [], []
    g_rows, g_cols = [], []

    # 2. Iterate through the crop
    rows, cols = data.shape
    for r in range(rows):
        for c in range(cols):
            if not pixel_mask[r, c]:
                # Get map coordinates of the pixel center
                x_center, y_center = out_transform * (c + 0.5, r + 0.5)
                
                # Convert map coordinates to GLOBAL indices (relative to original src)
                global_row, global_col = src.index(x_center, y_center)
                
                # Calculate polygon corners using out_transform
                ul_x, ul_y = out_transform * (c, r)
                lr_x, lr_y = out_transform * (c + 1, r + 1)
                
                geometries.append(box(ul_x, lr_y, lr_x, ul_y))
                pop_values.append(int(data[r, c]))
                global_ids.append(f"R{global_row}_C{global_col}")
                g_rows.append(global_row)
                g_cols.append(global_col)

    # 3. Create the GeoDataFrame
    results_gdf = gpd.GeoDataFrame({
        'cell_id': global_ids,
        'global_row': g_rows,
        'global_col': g_cols,
        'pop_count': pop_values,
        'geometry': geometries
    }, crs=src.crs)
   
# Save and Index
results_gdf.set_index('cell_id', inplace=True)
results_gdf.to_file(output_geojson, driver='GeoJSON')
print(f"Exported {len(results_gdf)} cells with Global IDs.")