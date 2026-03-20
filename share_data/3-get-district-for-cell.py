import geopandas as gpd

geojson_file = "detail_pois.geojson"
cell_gdf = gpd.read_file(geojson_file)

# Load the Vietnam District shapefile
districts = gpd.read_file("../map/gadm41_SGP_shp/gadm41_SGP_1.shp")
print(districts.crs)

# Ensure 'district' column exists
if 'district_name' not in cell_gdf.columns:
    cell_gdf['district_name'] = None

if 'district' not in cell_gdf.columns:
    cell_gdf['district'] = None

# Set the index to 'cell_id' for easier access
cell_gdf.set_index('cell_id', inplace=True)

# Ensure both use the same CRS
cell_gdf = cell_gdf.to_crs(districts.crs)

# Create centroids
cell_gdf['centroid'] = cell_gdf.geometry.centroid

# Create a temporary GeoDataFrame with centroids as geometry
centroid_gdf = cell_gdf.copy()
centroid_gdf.set_geometry('centroid', inplace=True)

# Perform spatial join to find districts
print("Performing spatial join...")
joined = gpd.sjoin(centroid_gdf, districts, how="left", predicate="within")
print(f"Join completed. Joined shape: {joined.shape}")

print(joined.columns.tolist())

# Update the original cell_gdf with district info
cell_gdf['district_name'] = joined['NAME_1']  # Assuming NAME_2 is district name
cell_gdf['district'] = joined["GID_1"]
print(f"Updated districts. Sample: {cell_gdf['district'].head()}")

# Drop the centroid column as it's not needed for saving
cell_gdf = cell_gdf.drop(columns=['centroid'])
cell_gdf = cell_gdf[cell_gdf['district'].notna()]

# Reset index if needed for saving
cell_gdf.reset_index(inplace=True)

# Save the updated GeoJSON  
print("Saving file...")
try:
    cell_gdf.to_file(geojson_file, driver='GeoJSON')
    print("District assignment completed. Saved to", geojson_file)
except Exception as e:
    print(f"Error saving file: {e}")