import pandas as pd
import geopandas as gpd
import numpy as np
from get_shape_city import get_geometry
from shapely.ops import unary_union
import osmnx as ox

shape_gdf = get_geometry()

print(shape_gdf)

boundary = shape_gdf.unary_union
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
joined = gpd.sjoin(all_pois, shape_gdf, how="inner", predicate="within")

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
counts = joined.groupby(['SUBZONE_C', 'poi_category']).size().unstack(fill_value=0)

# 7. Merge counts back to the original grid
final_gdf = shape_gdf.merge(counts, on='SUBZONE_C', how='left').fillna(0)

# Save result
final_gdf.to_file("detail_pois.geojson", driver='GeoJSON')
print("Done! Detailed counts saved.")
