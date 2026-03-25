import pandas as pd

# 1. Load your GeoJSON data
# Replace 'in_flow_cells_v2_distance.json' with your actual file path
gdf = pd.read_csv('categorized_cell_pairs_radiation_pair_amount.csv')
gdf = gdf[gdf['in_amount'] > 0]

# 2. Calculate the total sum of all inflows
total_in_flow = gdf['in_amount'].sum()

# 3. Normalize each in_amount by the total sum
# This gives you the proportion of total flow for each cell
gdf['norm_total_in'] = gdf['in_amount'] / total_in_flow

# 4. Optional: Verify the sum of normalized values is 1.0
print(f"Total In-Amount: {total_in_flow}")
print(f"Sum of Normalized: {gdf['norm_total_in'].sum()}")

gdf.sort_values(["cell_id", "subzone_id"])
gdf = gdf[['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id', 'norm_total_in']]
# 5. Save the updated data to a new file
gdf.to_csv('normalized_gen_flow.csv', index=False)

# Display the first few rows to verify
