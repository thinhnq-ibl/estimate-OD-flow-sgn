import geopandas as gpd

gdf = gpd.read_file("amount_out_from_cell.geojson")

# 1. Group by cell_id and sum the final_value
# This creates a Series where the index is the cell_id
cell_sums = gdf.groupby('cell_id')['final_out_value'].sum().reset_index()

# 2. To keep the Geometry, we need to merge this back to a unique list of cells
# We drop duplicates of cell_id from the original gdf first
unique_cells = gdf.drop_duplicates('cell_id').drop(columns=['final_out_value'])

# 3. Merge the summed values back
final_gdf = unique_cells.merge(cell_sums, on='cell_id')
final_gdf = final_gdf.drop(columns=["SUBZONE_C", "intersect_area_m2", "total_out_to_divide", "group_area", "district", "district_name"])
# Save the result
final_gdf.to_file("final_summed_out_cells.geojson", driver='GeoJSON')

print(final_gdf[['cell_id', 'final_out_value']].head())