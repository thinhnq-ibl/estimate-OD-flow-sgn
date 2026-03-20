import geopandas as gpd
import pandas as pd

# Read the shapes (subzones) and the grid of cells once
subzones = gpd.read_file('../map/sub_zone/data_sgp_subzone.shp')
grid = gpd.read_file('../share_data/city_grid.geojson')

results_list = []

# Use a projected CRS for accurate area calculations (meters)
PROJECTED_EPSG = 5179

# Pre-project grid to metric CRS once
grid_metric = grid.to_crs(epsg=PROJECTED_EPSG)

for idx, subzone_row in subzones.iterrows():
    # Create GeoDataFrame for this single subzone and project it
    boundary = gpd.GeoDataFrame([subzone_row], crs=subzones.crs)
    boundary_metric = boundary.to_crs(epsg=PROJECTED_EPSG)

    # Compute exact intersection geometries and areas in metric CRS
    intersections_metric = gpd.overlay(grid_metric, boundary_metric, how='intersection')
    if len(intersections_metric):
        intersections_metric['intersect_area_m2'] = intersections_metric.geometry.area
        # Filter for area above threshold
        # filtered = intersections_metric[intersections_metric['intersect_area_m2'] >= 1e-5]
        # if not filtered.empty:
        #     results_list.append(filtered)
        results_list.append(intersections_metric)
    else:
        print("No intersections for this subzone")

# Concat results and write to GeoJSON (keep original CRS)
if results_list:
    final_gdf = pd.concat(results_list, ignore_index=True)
    final_gdf.to_file("all_bounded_in_cells.geojson", driver='GeoJSON')
else:
    print("No bounded cells collected; nothing to write.")
