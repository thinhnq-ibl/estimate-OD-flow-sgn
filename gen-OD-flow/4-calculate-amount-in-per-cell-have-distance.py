import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation.csv"
pair_cell_gdf = pd.read_csv(csv_file)

geojson_file2 = "final_summed_out_cells.geojson"
out_data = gpd.read_file(geojson_file2)

# Ensure 'in_prob' column exists
pair_cell_gdf['in_amount'] = 0.0

# Extract the first cell_id as a scalar value (not a Series) FAST VECTORIZATION
out_amount_dict = out_data.set_index('cell_id')['in_amount'].astype(float).to_dict()
pair_cell_gdf['in_amount'] = pair_cell_gdf['cell_id'].map(out_amount_dict) * pair_cell_gdf['in_prob'].astype(float)

pair_cell_gdf = pair_cell_gdf.groupby(['cell_id', 'neighbor_id'], as_index=False)['in_amount'].sum()
pair_cell_gdf.to_csv(csv_file, index=False)