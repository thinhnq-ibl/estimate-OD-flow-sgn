import geopandas as gpd
import pandas as pd

# Read the shapes (subzones) and the grid of cells once
subzones = gpd.read_file('../map/sub_zone/data_sgp_subzone.shp')
grid = gpd.read_file('../share_data/city_grid.geojson')

results_list = []

# Use a projected CRS for accurate area calculations (meters)
PROJECTED_EPSG = 3414

# Pre-project grid to metric CRS once
grid_metric = grid.to_crs(epsg=PROJECTED_EPSG)
subzones = subzones.to_crs(epsg=PROJECTED_EPSG)

subzones_no_overlap = []

for idx, subzone_row in subzones.iterrows():
    # Create GeoDataFrame for this single subzone and project it
    boundary = gpd.GeoDataFrame([subzone_row], crs=subzones.crs)
    boundary_metric = boundary.to_crs(epsg=PROJECTED_EPSG)

    # Compute exact intersection geometries and areas in metric CRS
    intersections_metric = gpd.overlay(grid_metric, boundary_metric, how='intersection')
    # print(intersections_metric.columns)
    if len(intersections_metric):
        intersections_metric['intersect_area_m2'] = intersections_metric.geometry.area
        results_list.append(intersections_metric)
    else:
        subzones_no_overlap.append(subzone_row)
        print("No intersections for this subzone", subzone_row["SUBZONE_C"], intersections_metric["cell_id"].tolist())

# Concat results and write to GeoJSON (keep original CRS)
if results_list:
    final_gdf = pd.concat(results_list, ignore_index=True)
    final_gdf.to_file("all_bounded_in_cells.geojson", driver='GeoJSON')
    subzones_no_overlap_gdf = pd.DataFrame(subzones_no_overlap)
    subzones_no_overlap_gdf.to_csv("subzones_no_overlap.csv", index=False)
else:
    print("No bounded cells collected; nothing to write.")
