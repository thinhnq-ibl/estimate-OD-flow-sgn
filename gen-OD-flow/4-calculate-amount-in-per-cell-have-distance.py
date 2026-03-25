import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation.csv"
pair_cell_gdf = pd.read_csv(csv_file)

geojson_file2 = "final_summed_out_cells.geojson"
out_data = gpd.read_file(geojson_file2)

# Ensure 'in_prob' column exists
pair_cell_gdf['in_amount'] = 0.0

# FAST VECTORIZATION: Use merge instead of apply for massive speedup
# Prepare out_data for merge
out_subset = out_data[['cell_id', 'SUBZONE_C', 'out_amount']].copy()
out_subset.rename(columns={'SUBZONE_C': 'subzone_id'}, inplace=True)

# Merge to map out_amount to each pair based on origin cell
pair_cell_gdf = pair_cell_gdf.merge(out_subset, on=['cell_id', 'subzone_id'], how='left')
pair_cell_gdf['in_amount'] = pair_cell_gdf['out_amount'].fillna(0) * pair_cell_gdf['in_prob']

# Final grouping to ensure unique pairs (optional but safe)
pair_cell_gdf = pair_cell_gdf.groupby(['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id'], as_index=False)['in_amount'].sum()
pair_cell_gdf.to_csv("categorized_cell_pairs_radiation_pair_amount.csv", index=False)