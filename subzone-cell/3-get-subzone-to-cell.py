import geopandas as gpd
from get_shape_city import get_geometry
import pandas as pd
import warnings


geojson_file = "detail_pois.geojson"
cell_gdf = gpd.read_file(geojson_file)

singapore_gdf = get_geometry()

# join cell_gdf with singapore_gdf to know which district each cell belongs to
# if cell is in multiple districts, assign to the district with the largest area


warnings.filterwarnings('ignore', 'GeoSeries.notna', UserWarning)

if singapore_gdf.crs != cell_gdf.crs:
    singapore_gdf = singapore_gdf.to_crs(cell_gdf.crs)

# 1. Overlay to find intersections
overlay = gpd.overlay(cell_gdf, singapore_gdf, how='intersection')

# Calculate area (convert to EPSG:3414 for accurate area in square meters for Singapore)
# Even if data is for SGN, EPSG:3414 or EPSG:3857 works better than EPSG:4326 for area comparison
overlay['intersection_area'] = overlay.to_crs(epsg=3414).geometry.area

# Sort by cell_id and intersection area, keep the all 
overlay = overlay.sort_values(by=['cell_id', 'intersection_area'], ascending=[True, False])

# Merge back to original cells to keep original geometry
cols_to_merge = [col for col in singapore_gdf.columns if col != 'geometry']
assigned_cells = cell_gdf.merge(
    overlay[['cell_id'] + cols_to_merge + ['intersection_area']],
    on='cell_id',
    how='inner'
)

# 2. if cell is not in any district, assign to the nearest district
unassigned_cells = cell_gdf[~cell_gdf['cell_id'].isin(assigned_cells['cell_id'])].copy()

if not unassigned_cells.empty:
    unassigned_cells_proj = unassigned_cells.to_crs(epsg=3414)
    singapore_gdf_proj = singapore_gdf.to_crs(epsg=3414)
    
    # Nearest neighbor join
    nearest_join = gpd.sjoin_nearest(unassigned_cells_proj, singapore_gdf_proj, how='left', distance_col='distance')
    
    # Drop duplicates if multiple targets are at exact same minimum distance
    nearest_join = nearest_join.sort_values(by=['cell_id', 'distance']).drop_duplicates(subset=['cell_id'])
    
    # Merge the subzone info back into unassigned_cells
    cols_to_merge = [col for col in singapore_gdf.columns if col != 'geometry']
    newly_assigned_cells = unassigned_cells.merge(
        nearest_join[['cell_id'] + cols_to_merge],
        on='cell_id',
        how='left'
    )
    
    final_cell_gdf = pd.concat([assigned_cells, newly_assigned_cells], ignore_index=True)
else:
    final_cell_gdf = assigned_cells

# keep row have intersection area > 10% of the cell area, to avoid assigning a cell to a district just because it has a tiny sliver of intersection
final_cell_gdf['cell_area'] = final_cell_gdf.to_crs(epsg=3414).geometry.area
final_cell_gdf = final_cell_gdf[final_cell_gdf['intersection_area'] / final_cell_gdf['cell_area'] > 0.045].copy()

# Save the final geodataframe
output_file = "detail_pois_district.geojson"
final_cell_gdf.to_file(output_file, driver="GeoJSON")
print(f"Successfully processed {len(final_cell_gdf)} cells and saved to {output_file}")
