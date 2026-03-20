import geopandas as gpd
import pandas as pd

# 1. Load and Project
gdf = gpd.read_file('final_summed_out_cells.geojson').reset_index()
gdf = gdf.to_crs(epsg=5179) 

# 2. Define thresholds
threshold_near = 10000  # 1km
threshold_far = 10 * 10000  # 10km
threshold_over = 20 * 10000   # 20km

# 3. Create a buffer for the maximum search area (10km)
# We keep 'cell_id' in this copy so it's available after the join
gdf_buffered = gdf[['cell_id', 'geometry']].copy()

# 6. Calculate exact distance to categorize
def calculate_distance(row, row2):
    # Lookup the original geometries using the cell_ids
    geom_a = row.geometry 
    geom_b = row2.geometry
    return geom_a.distance(geom_b)

result = []

for index, row in gdf.iterrows():
    for index2, row2 in gdf.iterrows():
        result.append({
            "cell_id": row["cell_id"],
            "neighbor_id": row2["cell_id"],
            "distance_m": calculate_distance(row, row2)
        })


# # 8. Export
# output_gdf = nearby.to_crs(epsg=4326)

result_df = pd.DataFrame(result)
# 7. Categorize
result_df['category'] = 'too-far'
result_df.loc[result_df['distance_m'] <= threshold_over, 'category'] = '10km-20km'
result_df.loc[result_df['distance_m'] <= threshold_far, 'category'] = '1km-10km'
result_df.loc[result_df['distance_m'] <= threshold_near, 'category'] = 'under_1km'

result_df = result_df[(result_df['category'] == '10km-20km') | (result_df['category'] == '1km-10km') | (result_df['category'] == 'under_1km')]

result_df.to_csv("categorized_cell_pairs.csv")

# print(output_gdf[['cell_id', 'neighbor_id', 'distance_m', 'category']].head())