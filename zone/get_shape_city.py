import geopandas as gpd
# import matplotlib.pyplot as plt

def get_geometry():

    # 1. Load the original Vietnam district-level file
    vnm_city = gpd.read_file("../map/sub_zone/data_sgp_subzone.shp")
    print(vnm_city)
    # fig, ax = plt.subplots(figsize=(7, 7))
    # vnm_city.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
    # ax.set_title(f"Seoul Boundary")
    # plt.show()
    return vnm_city

