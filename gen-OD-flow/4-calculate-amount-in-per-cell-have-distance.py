import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation.csv"
pair_cell_gdf = pd.read_csv(csv_file)

out_data = gpd.read_file("../zone/pop_grid.geojson")

out_amount = pd.read_csv("../map/data_trip_sum.csv", usecols=['ORIGIN_SUBZONE','DESTINATION_SUBZONE','COUNT'])
out_amount = out_amount.groupby('ORIGIN_SUBZONE')['COUNT'].sum().reset_index()

# merge to get out_amount for each subzone
out_data = out_data.merge(out_amount, left_on='SUBZONE_C', right_on='ORIGIN_SUBZONE', how='left')
out_data['out_amount'] = out_data['COUNT'].fillna(0)  # Fill NaN with 0 for cells with no outflow
out_data.drop(columns=['ORIGIN_SUBZONE', 'COUNT'], inplace=True)  # Clean   

# Ensure 'in_prob' column exists
pair_cell_gdf['in_amount'] = 0.0

# FAST VECTORIZATION: Use merge instead of apply for massive speedup
# Prepare out_data for merge
out_subset = out_data[['SUBZONE_C', 'out_amount']].copy()
out_subset.rename(columns={'SUBZONE_C': 'subzone_id'}, inplace=True)

# Merge to map out_amount to each pair based on origin cell
pair_cell_gdf = pair_cell_gdf.merge(out_subset, on='subzone_id', how='left')
pair_cell_gdf['in_amount'] = pair_cell_gdf['out_amount'].fillna(0) * pair_cell_gdf['in_prob']

# Final grouping to ensure unique pairs (optional but safe)
pair_cell_gdf = pair_cell_gdf.groupby(['subzone_id', 'neighbor_subzone_id'], as_index=False)['in_amount'].sum()
pair_cell_gdf.to_csv("categorized_cell_pairs_radiation_pair_amount.csv", index=False)