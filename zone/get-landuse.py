import pandas as pd
import rasterio.mask
import rasterio.features
import geopandas as gpd
import numpy as np
from shapely.geometry import box
from get_shape_city import get_geometry
from shapely.ops import unary_union
import osmnx as ox

tags = {"landuse": True} 
shape_gdf = get_geometry()

print(shape_gdf)

boundary = shape_gdf.unary_union
tags = {"landuse": True} 

print("Downloading landuse for the entire area...")
all_landuse = ox.features_from_polygon(boundary, tags)

# 3. Clean the POI data
# OSMnx returns points, lines, and polygons. We'll convert everything to points (centroids)
# to make sure they fall neatly into a grid cell.
all_landuse['geometry'] = all_landuse.centroid

# 4. Spatial Join: Link each POI to a cell_id
# This creates a row for every POI-Cell intersection
joined = gpd.sjoin(all_landuse, shape_gdf, how="inner", predicate="within")

# 6. Pivot Table
# Count occurrences of each category per cell_id
counts = joined.groupby(['SUBZONE_C', 'landuse']).size().unstack(fill_value=0)

# 7. Merge counts back to the original grid
final_gdf = shape_gdf.merge(counts, on='SUBZONE_C', how='left').fillna(0)

# Save result
final_gdf.to_file("detail_landuse.geojson", driver='GeoJSON')
print("Done! Detailed counts saved.")
