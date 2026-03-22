import geopandas as gpd
import pandas as pd
gdf = gpd.read_file('../subzone-cell/detail_pois_district.geojson').reset_index()
out_data = pd.read_csv('../gen-cell-flow-for-test/only_cell_out.csv')

# Vectorized fast mapping instead of O(N^2) inner loop filter
out_amount_dict = out_data.set_index('origin_cell_id')['flow_count'].to_dict()
result = []
for _, row in out_data.iterrows():
    # distribute flow to cell by intersection area
    list_cell = gdf[gdf['cell_id'] == row['origin_cell_id']]
    total_intersection_area = list_cell['intersection_area'].sum()
    for _, cell_row in list_cell.iterrows():
        cell_row['out_amount'] = cell_row['intersection_area'] / total_intersection_area * row['flow_count']
        result.append(cell_row)

# save gdf to csv
result_gdf = gpd.GeoDataFrame(result)
result_gdf.to_file("final_summed_out_cells.geojson", driver='GeoJSON')
