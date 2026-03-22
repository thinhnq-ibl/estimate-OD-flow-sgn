import pandas as pd

# 1. Load your GeoJSON data
# Replace 'in_flow_cells_v2_distance.json' with your actual file path
gdf = pd.read_csv('all_flow_cell33.csv')
gdf = gdf[gdf['flow_count'] > 0]

# 2. Calculate the total sum of all inflows
total_in_flow = gdf['flow_count'].sum()

# 3. Normalize each in_amount by the total sum
# This gives you the proportion of total flow for each cell
gdf['norm_total_in'] = gdf['flow_count'] / total_in_flow

# 4. Optional: Verify the sum of normalized values is 1.0
print(f"Total Flow: {total_in_flow}")
print(f"Sum of Normalized: {gdf['norm_total_in'].sum()}")

gdf.sort_values("origin_cell_id")
gdf = gdf[['origin_cell_id', 'destination_cell_id', 'norm_total_in']]
# 5. Save the updated data to a new file
# change name origin_cell_id to cell_id and destination_cell_id to neighbor_id
gdf.rename(columns={'origin_cell_id': 'cell_id', 'destination_cell_id': 'neighbor_id'}, inplace=True)
gdf.to_csv('normalized_real_flow.csv', index=False)

# Display the first few rows to verify
