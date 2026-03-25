import geopandas as gpd
import pandas as pd

csv_file = "categorized_cell_pairs_radiation_pair_amount.csv"
pair_cell_gdf = pd.read_csv(csv_file)

print(pair_cell_gdf['in_amount'].sum())

csv_file2 = "categorized_cell_pairs_radiation.csv"
pair_cell_gdf2 = pd.read_csv(csv_file2)

pair_cell_gdf2['sum_in_prob'] = pair_cell_gdf2.groupby('subzone_id')['in_prob'].transform('sum')
# find pairs where sum_in_prob < 1 and print them out
incomplete_prob_pairs = pair_cell_gdf2[pair_cell_gdf2['sum_in_prob'] < 0.9999]
print(incomplete_prob_pairs[['subzone_id', 'sum_in_prob']].drop_duplicates())