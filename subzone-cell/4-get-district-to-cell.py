# get district_zone.csv from map folder
# get detail_pois_2.geojson from 3-get-district-to-cell.py
# merge them to get final_pois_2.geojson to get district for each cell by subzone

import pandas as pd
import geopandas as gpd

# Load the files
district_zone_df = pd.read_csv("../map/district_zone.csv")
detail_pois_gdf = gpd.read_file("detail_pois_district.geojson")

# Merge detail_pois_gdf and district_zone_df
# detail_pois_gdf has 'SUBZONE_C', which matches 'zone_id' in district_zone_df
final_pois_gdf = detail_pois_gdf.merge(district_zone_df, left_on="SUBZONE_C", right_on="zone_id", how="left")

# Save the final geodataframe
final_pois_gdf.to_file("detail_pois_district.geojson", driver="GeoJSON")
print("Successfully processed and saved to detail_pois_district.geojson")