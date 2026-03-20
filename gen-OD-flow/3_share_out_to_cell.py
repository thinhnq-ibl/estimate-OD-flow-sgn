import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

gdf = gpd.read_file('all_bounded_out_cells.geojson')

# Example: Different amounts for different indices
origin_count = pd.read_csv('aggregated_origin_counts.csv')
amounts_map = {}
for index, row in origin_count.iterrows():
    amounts_map[row["ORIGIN_SUBZONE"]] = row["COUNT"]

# Map the total amount to each row
gdf['total_out_to_divide'] = gdf['SUBZONE_C'].map(amounts_map)

# Calculate the count per group
gdf['group_area'] = gdf.groupby('SUBZONE_C')['intersect_area_m2'].transform('sum')

# Divide
gdf['final_out_value'] = gdf['total_out_to_divide'] / gdf['group_area'] * gdf["intersect_area_m2"] 

gdf.to_file("amount_out_from_cell.geojson", driver='GeoJSON')

