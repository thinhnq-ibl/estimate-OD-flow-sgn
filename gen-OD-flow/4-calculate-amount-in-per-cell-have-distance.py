import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation.csv"
pair_cell_gdf = pd.read_csv(csv_file)

geojson_file2 = "final_summed_out_cells.geojson"
out_data = gpd.read_file(geojson_file2)

# Ensure 'in_prob' column exists
pair_cell_gdf['in_amount'] = 0.0

# Extract the first cell_id as a scalar value (not a Series) FAST VECTORIZATION
out_amount_dict = out_data.set_index(['cell_id', 'SUBZONE_C'])['out_amount'].astype(float).to_dict()
pair_cell_gdf['in_amount'] = pair_cell_gdf[['cell_id', 'subzone_id']].apply(lambda x: out_amount_dict.get((x['cell_id'], x['subzone_id']), 0), axis=1) * pair_cell_gdf['in_prob'].astype(float)   

pair_cell_gdf = pair_cell_gdf.groupby(['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id'], as_index=False)['in_amount'].sum()
pair_cell_gdf.to_csv("categorized_cell_pairs_radiation_pair_amount.csv", index=False)