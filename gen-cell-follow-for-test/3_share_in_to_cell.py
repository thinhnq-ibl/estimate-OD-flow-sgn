import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

gdf = gpd.read_file('all_bounded_in_cells.geojson')

# Example: Different amounts for different indices
origin_count = pd.read_csv('aggregated_destination_counts.csv')
amounts_map = {}
for index, row in origin_count.iterrows():
    amounts_map[row["DESTINATION_SUBZONE"]] = row["COUNT"]

# print(amounts_map)

# Map the total amount to each row
gdf['total_in_to_divide'] = gdf['SUBZONE_C'].map(amounts_map)

# Calculate the count per group
gdf['group_area'] = gdf.groupby('SUBZONE_C')['intersect_area_m2'].transform('sum')

# Divide
gdf['cell_in'] = gdf['total_in_to_divide'] / gdf['group_area'] * gdf["intersect_area_m2"]

gdf.to_file("all_bounded_in_cells.geojson", driver='GeoJSON')


