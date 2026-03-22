import geopandas as gpd
import pandas as pd
import numpy as np
import os

# 1. Load and Project
base_dir = os.path.dirname(os.path.abspath(__file__))

# ORIGINS: Only cells that actually have trips leaving (active origins)
gdf_origin = gpd.read_file(os.path.join(base_dir, 'final_summed_out_cells.geojson')).reset_index()
gdf_origin = gdf_origin.to_crs(epsg=3414) # Singapore SVY21

# DESTINATIONS: ALL cells in the grid, so we don't miss pure destination cells (e.g. industrial areas with 0 pop)
gdf_dest = gpd.read_file(os.path.join(base_dir, '../subzone-cell/detail_pois_district.geojson')).reset_index()
gdf_dest = gdf_dest.to_crs(epsg=3414)

# 2. Define thresholds in meters
threshold_near = 1000  # 1km
threshold_far = 10000  # 10km
threshold_over = 100000   # 100km

result = []

print(f"Calculating distances between {len(gdf_origin)} origins and {len(gdf_dest)} destinations...")

# 6. Vectorized distance calculation
for index, row in gdf_origin.iterrows():
    # Calculate distance from this origin to ALL destinations at once
    # (using centroids is standard for grid cell models)
    distances = gdf_dest.geometry.centroid.distance(row.geometry.centroid)
    
    # Filter by max threshold to keep file size manageable (exclude > 100km)
    mask = distances <= threshold_over
    
    if mask.any():
        valid_dests = gdf_dest[mask]
        valid_dists = distances[mask]
        
        # Create a dataframe for this batch
        batch_df = pd.DataFrame({
            "cell_id": row["cell_id"],
            "subzone_id": row["SUBZONE_C"],
            "neighbor_id": valid_dests["cell_id"].values,
            "neighbor_subzone_id": valid_dests["SUBZONE_C"].values,
            "distance_m": valid_dists.values
        })
        result.append(batch_df)

result_df = pd.concat(result, ignore_index=True)
# 7. Categorize
result_df['category'] = 'too-far'
result_df.loc[result_df['distance_m'] <= threshold_over, 'category'] = '10km-100km'
result_df.loc[result_df['distance_m'] <= threshold_far, 'category'] = '1km-10km'
result_df.loc[result_df['distance_m'] <= threshold_near, 'category'] = 'under_1km'

result_df = result_df[(result_df['category'] == '10km-100km') | (result_df['category'] == '1km-10km') | (result_df['category'] == 'under_1km')]

out_file = os.path.join(base_dir, "categorized_cell_pairs.csv")
result_df.to_csv(out_file, index=False)
print(f"Saved {len(result_df)} pairs to {out_file}")