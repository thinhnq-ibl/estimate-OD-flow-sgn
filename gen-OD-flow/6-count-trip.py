import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation_pair_amount.csv"
pair_cell_gdf = pd.read_csv(csv_file)

print(pair_cell_gdf['in_amount'].sum())

gdf = gpd.read_file('final_summed_out_cells.geojson').reset_index()
print(gdf['out_amount'].sum())