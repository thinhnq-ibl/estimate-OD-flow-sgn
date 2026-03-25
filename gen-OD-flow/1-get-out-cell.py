import geopandas as gpd
import pandas as pd
gdf = gpd.read_file('../subzone-cell/detail_pois_district.geojson').reset_index()
out_data = pd.read_csv('../gen-cell-flow-for-test/only_cell_out.csv')

# Vectorized fast merge instead of slow iterative loop
result_gdf = gdf.merge(out_data[['origin_cell_id', 'origin_subzone_id', 'flow_count']], 
                       left_on=['cell_id', 'SUBZONE_C'], 
                       right_on=['origin_cell_id', 'origin_subzone_id'], 
                       how='inner')

# Rename flow_count to out_amount and clean up merged keys
result_gdf.rename(columns={'flow_count': 'out_amount'}, inplace=True)
result_gdf.drop(columns=['origin_cell_id', 'origin_subzone_id'], inplace=True)
result_gdf.to_file("final_summed_out_cells.geojson", driver='GeoJSON')
