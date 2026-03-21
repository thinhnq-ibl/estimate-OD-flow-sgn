import geopandas as gpd
import pandas as pd
gdf = gpd.read_file('../subzone-cell/final_pois_2.geojson').reset_index()
out_data = pd.read_csv('../gen-cell-flow-for-test/only_cell_out.csv')

# find the cell_id in out_data and write in_amount to gdf

for index, row in out_data.iterrows():
    gdf.loc[gdf['cell_id'] == row['cell_id'], 'in_amount'] = row['in_amount']

# save gdf to csv
gdf.to_file("final_summed_out_cells.geojson", driver='GeoJSON')

