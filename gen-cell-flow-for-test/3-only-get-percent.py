import pandas as pd
import gc

# 1. Load data with optimal usecols
gdf = pd.read_csv('../map/data_trip_sum.csv', usecols=['ORIGIN_SUBZONE','DESTINATION_SUBZONE','COUNT'])
gdf = gdf[gdf['COUNT'] > 0]

# 2. Calculate the global total sum
total_in_flow = gdf['COUNT'].sum()

# 3. Normalize each flow_count by the global total
gdf['norm_total_in'] = gdf['COUNT'] / total_in_flow

# 4. Optional: Verify the sum of normalized values is expected
print(f"Total Flow: {total_in_flow}")
print(f"Sum of Normalized: {gdf['norm_total_in'].sum()}")

# Drop unused columns to free memory before sort
gdf.drop(columns=['COUNT'], inplace=True)

# 5. Sort inplace and save the updated data to a new file
gdf.sort_values(['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE'], inplace=True)

gdf.to_csv('normalized_real_flow.csv', index=False)
