import osmnx as ox
import geopandas as gpd
import pandas as pd

# 1. Load your grid
grid_gdf = gpd.read_file("city_grid.geojson")

# 2. Get all POIs for the entire area covered by the grid
# We use the unary_union of your grid to get the total boundary
boundary = grid_gdf.unary_union
tags = {
    'amenity': True, 'shop': True, 'tourism': True,
    'leisure': True, 'office': True, 'public_transport': True
}

print("Downloading POIs for the entire area...")
all_pois = ox.features_from_polygon(boundary, tags)

# 3. Clean the POI data
# OSMnx returns points, lines, and polygons. We'll convert everything to points (centroids)
# to make sure they fall neatly into a grid cell.
all_pois['geometry'] = all_pois.centroid
# Keep only the columns that match our tags
poi_columns = [col for col in tags.keys() if col in all_pois.columns]

# 4. Spatial Join: Link each POI to a cell_id
# This creates a row for every POI-Cell intersection
joined = gpd.sjoin(all_pois, grid_gdf, how="inner", predicate="within")

# 5. Count by Type
# We need to identify which tag triggered the POI. 
# We'll create a 'poi_type' column based on which tag column is not null.
def get_poi_type(row):
    for tag in tags.keys():
        if pd.notnull(row.get(tag)):
            return tag
    return 'other'

joined['poi_category'] = joined.apply(get_poi_type, axis=1)

# 6. Pivot Table
# Count occurrences of each category per cell_id
counts = joined.groupby(['cell_id', 'poi_category']).size().unstack(fill_value=0)

# 7. Merge counts back to the original grid
final_gdf = grid_gdf.merge(counts, on='cell_id', how='left').fillna(0)

# Save result
final_gdf.to_file("detail_pois.geojson", driver='GeoJSON')
print("Done! Detailed counts saved.")