import geopandas as gpd
# import matplotlib.pyplot as plt

def get_geometry():

    
    # 1. Load the original Vietnam district-level file
    vnm_city = gpd.read_file("../map/gadm36_SGP_shp/gadm36_SGP_1.shp")

    # 2. Get HCM shape
    # db_seoul = vnm_city[vnm_city['GID_1'].str.contains("SGP.1", case=False, na=False)]
    db_seoul = vnm_city
    print(db_seoul[["GID_1","NAME_1"]])

    # fig, ax = plt.subplots(figsize=(7, 7))
    # db_seoul.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
    # ax.set_title(f"Seoul Boundary")
    # plt.show()

    return db_seoul

def get_geometry2():

    # 1. Load the original Vietnam district-level file
    vnm_city = gpd.read_file("../map/sub_zone/data_sgp_subzone.shp")
    print(vnm_city)
    # fig, ax = plt.subplots(figsize=(7, 7))
    # vnm_city.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
    # ax.set_title(f"Seoul Boundary")
    # plt.show()
    return vnm_city

def get_geometry3():

    # 1. Load the original Vietnam district-level file
    vnm_city = gpd.read_file("../map/gadm41_SGP_shp/gadm41_SGP_1.shp")
    # print(vnm_city.columns)
    # fig, ax = plt.subplots(figsize=(7, 7))
    # vnm_city.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
    # ax.set_title(f"Seoul Boundary")
    # plt.show()
    return vnm_city

get_geometry()
get_geometry2()
get_geometry3()