import pandas as pd
import gc

# 1. Load data with optimal usecols
usecols = ['origin_cell_id', 'origin_subzone_id', 'destination_cell_id', 'destination_subzone_id', 'flow_count']
gdf = pd.read_csv('all_flow_cell_with_subzone.csv', usecols=usecols)
gdf = gdf[gdf['flow_count'] > 0]

# 2. Calculate the global total sum
total_in_flow = gdf['flow_count'].sum()

# 3. Normalize each flow_count by the global total
gdf['norm_total_in'] = gdf['flow_count'] / total_in_flow

# 4. Optional: Verify the sum of normalized values is expected
print(f"Total Flow: {total_in_flow}")
print(f"Sum of Normalized: {gdf['norm_total_in'].sum()}")

# Drop unused columns to free memory before sort
gdf.drop(columns=['flow_count'], inplace=True)

# 5. Sort inplace and save the updated data to a new file
gdf.sort_values(['origin_cell_id', 'origin_subzone_id'], inplace=True)

# change name origin_cell_id to cell_id and destination_cell_id to neighbor_id
gdf.rename(columns={'origin_cell_id': 'cell_id', 'origin_subzone_id': 'subzone_id', 'destination_cell_id': 'neighbor_id', 'destination_subzone_id': 'neighbor_subzone_id'}, inplace=True)
gdf.to_csv('normalized_real_flow.csv', index=False)
