import rasterio
import rasterio.mask
import rasterio.features
import geopandas as gpd
import numpy as np
from shapely.geometry import box
from get_shape_city import get_geometry
from shapely.ops import unary_union

tif_file = "../map/sgp_pop_2025_CN_1km_R2025A_UA_v1.tif"
output_geojson = "city_grid.geojson"

with rasterio.open(tif_file) as src:
    print(src.crs)
    singapore_gdf = get_geometry()
    
    # 1. Đồng bộ CRS
    singapore_gdf = singapore_gdf.to_crs(src.crs)

    # 2. Gom nhóm các đảo
    # geoms = [unary_union(singapore_gdf.geometry)]

    # 3. Dùng geometry_mask để bỏ qua nodata của dữ liệu dân số, chỉ lấy theo đúng shape.
    out_image, out_transform = rasterio.mask.mask(src, singapore_gdf.geometry, crop=True, filled=True, all_touched=True)

    data = out_image[0]
    
    # pixel_mask sẽ False (giữ lại) nếu cell nằm trong/chạm shape.
    pixel_mask = rasterio.features.geometry_mask(
        singapore_gdf.geometry,
        out_shape=data.shape,
        transform=out_transform,
        invert=False,
        all_touched=True
    )
    
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
                
                
                pop_val = data[r, c]
                if src.nodata is not None and pop_val == src.nodata:
                    pop_val = 0
                
                # if pop_val > 0:
                geometries.append(box(ul_x, lr_y, lr_x, ul_y))
                pop_values.append(int(pop_val))
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