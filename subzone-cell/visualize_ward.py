import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString
import pandas as pd
from shapely import wkt
from shapely.affinity import translate

# Define cell data and coordinates from GeoJSON

vnm_city2 = gpd.read_file("../map/gadm36_VNM_shp/gadm36_VNM_3.shp")
hcmc_boundary = vnm_city2[(vnm_city2["NAME_2"] == "Quận 1") | 
                          (vnm_city2["NAME_2"] == "Quận 10") | 
                            (vnm_city2["NAME_2"] == "Tân Bình") | 
                            (vnm_city2["NAME_2"] == "Bình Thạnh") | 
                            (vnm_city2["NAME_2"] == "Quận 5") |
                          (vnm_city2["NAME_2"] == "Quận 3")].copy()
# district_boundary = vnm_city2[vnm_city2['GID_2'] == 'VNM.25_1'].copy()

print(vnm_city2[vnm_city2["NAME_2"] == "Quận 1"].head())

print(hcmc_boundary.crs)

# load edge data from ../obser_data_2_4_25.csv
edge_data = pd.read_csv("../obser_data_2_4_25.csv")
print(edge_data.head())
# data have lat_st, lon_st, lat_en, lon_en
# Create a GeoDataFrame for edges by connecting start and end points
result = []
for index, row in edge_data.iterrows():
    print(row.iat[10], row.iat[11], row.iat[12], row.iat[13])
    line = LineString([(row.iat[11], row.iat[10]), (row.iat[13], row.iat[12])])
    result.append(line)

edge_data['geometry'] = result
gdf_edges = gpd.GeoDataFrame(edge_data, geometry='geometry', crs="EPSG:4326")
print(gdf_edges.head())


# Create Plot
fig, ax = plt.subplots(figsize=(30, 20))
# Plot city boundary
hcmc_boundary.boundary.plot(ax=ax, color='green', linewidth=2)
gdf_edges.plot(ax=ax, color='blue', linewidth=5, alpha=0.7)
# Label each cell
# for x, y, label in zip(gdf["centroid"].x, gdf["centroid"].y, gdf.cell_id):
#     ax.text(x, y, label, fontsize=12, ha='center', va='center', fontweight='bold')

plt.title("Grid Cell Geometry Map (Singapore)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("cell_geometries.png")