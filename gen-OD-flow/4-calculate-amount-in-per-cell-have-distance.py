import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation.csv"
pair_cell_gdf = pd.read_csv(csv_file)

geojson_file2 = "final_summed_out_cells.geojson"
out_data = gpd.read_file(geojson_file2)

# Ensure 'in_prob' column exists
pair_cell_gdf['in_amount'] = 0.0

# Extract the first cell_id as a scalar value (not a Series)
for index, row in pair_cell_gdf.iterrows():
    pois_data = out_data[out_data["cell_id"] == row["cell_id"]].iloc[0]
    pair_cell_gdf.at[index, "in_amount"] = float(pois_data["in_amount"]) * float(row["in_prob"])

pair_cell_gdf = pair_cell_gdf.groupby(['cell_id', 'neighbor_id'], as_index=False)['in_amount'].sum()
pair_cell_gdf.to_csv(csv_file, index=False)