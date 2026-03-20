import pandas as pd

# 1. Load your GeoJSON data
# Replace 'in_flow_cells_v2_distance.json' with your actual file path
gdf = pd.read_csv('all_flow_cell33.csv')

# 2. Calculate the total sum of all inflows
total_in_flow = gdf['in_amount'].sum()

# 3. Normalize each in_amount by the total sum
# This gives you the proportion of total flow for each cell
gdf['norm_total_in'] = gdf['in_amount'] / total_in_flow

# 4. Optional: Verify the sum of normalized values is 1.0
print(f"Total In-Amount: {total_in_flow}")
print(f"Sum of Normalized: {gdf['norm_total_in'].sum()}")

gdf.sort_values("cell_id")
gdf = gdf[['cell_id', 'neighbor_id', 'norm_total_in']]
# 5. Save the updated data to a new file
gdf.to_csv('normalized_real_flow.csv', index=False)

# Display the first few rows to verify
