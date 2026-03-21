import geopandas as gpd
import pandas as pd
gdf = gpd.read_file('../subzone-cell/final_pois_2.geojson').reset_index()
out_data = pd.read_csv('../gen-cell-flow-for-test/only_cell_out.csv')

# Vectorized fast mapping instead of O(N^2) inner loop filter
in_amount_dict = out_data.set_index('cell_id')['in_amount'].to_dict()
gdf['in_amount'] = gdf['cell_id'].map(in_amount_dict).fillna(0.0)

# save gdf to csv
gdf.to_file("final_summed_out_cells.geojson", driver='GeoJSON')

