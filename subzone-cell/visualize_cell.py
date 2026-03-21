import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import pandas as pd
from shapely import wkt
from shapely.affinity import translate

# Define cell data and coordinates from GeoJSON

vnm_city2 = gpd.read_file("../map/sub_zone/data_sgp_subzone.shp")

print(vnm_city2.crs)


vnm_city = gpd.read_file("../map/gadm41_SGP_shp/gadm41_SGP_1.shp")

lat_offset = 0 # Move North by 0.5 degrees
lon_offset = 0  # Move East by 1.2 degrees
# 3. Translate the shape
# In Shapely, 'x' is Longitude and 'y' is Latitude
# moved_city = translate(vnm_city, xoff=lon_offset, yoff=lat_offset)

vnm_city['geometry'] = vnm_city.translate(xoff=lon_offset, yoff=lat_offset)


# 2. Get Singapore shape
sgp_shape = vnm_city

data = gpd.read_file("city_grid.geojson")
features = data[["cell_id", "geometry"]]
gdf = gpd.GeoDataFrame(features)

# Concatenate grid and city boundary for plotting
plot_gdf = gdf 

# Project to a metric CRS for centroid calculation (only for grid cells)
gdf_proj = gdf.to_crs(epsg=4326)
gdf["centroid"] = gdf_proj.centroid.to_crs(gdf.crs)


# Create Plot
fig, ax = plt.subplots(figsize=(20, 10))
# Plot city boundary
sgp_shape.boundary.plot(ax=ax, color='blue', linewidth=2)
vnm_city2.boundary.plot(ax=ax, color='green', linewidth=2)
# Plot grid
gdf.boundary.plot(ax=ax, color='black', linewidth=1)
gdf.plot(ax=ax, color='skyblue', alpha=0.4)

# Label each cell
# for x, y, label in zip(gdf["centroid"].x, gdf["centroid"].y, gdf.cell_id):
#     ax.text(x, y, label, fontsize=12, ha='center', va='center', fontweight='bold')

plt.title("Grid Cell Geometry Map (Singapore)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("cell_geometries.png")