import geopandas as gpd
import pandas as pd

# Read the shapes (subzones) and the grid of cells once
trips = pd.read_csv('../share_data/aggregated_trips.csv')

all_cell = gpd.read_file("all_bounded_in_cells.geojson")

# keep only relevant columns but preserve the geometry column so the result stays a
# GeoDataFrame (needed for GeoPandas methods like `to_file`).
result = []

for _, row in trips.iterrows():
    all_sub_cell = all_cell[all_cell["SUBZONE_C"] == row["ORIGIN_SUBZONE"]]
    list_cell = all_sub_cell[["cell_id"]]
    sum_area = all_sub_cell["intersect_area_m2"].sum()
    list_cell["percent_area"] = all_sub_cell["intersect_area_m2"] / sum_area
    list_cell["in_amount"] = list_cell["percent_area"] * row["COUNT"]

    all_sub_out_cell = all_cell[all_cell["SUBZONE_C"] == row["DESTINATION_SUBZONE"]]
    list_out_cell = all_sub_out_cell[["cell_id"]]
    sum_out_area = all_sub_out_cell["intersect_area_m2"].sum()
    list_out_cell["percent_area"] = all_sub_out_cell["intersect_area_m2"] / sum_out_area


    for _, r1 in list_cell.iterrows():
        in_amount = r1["in_amount"]
        for _, r2 in list_out_cell.iterrows():
            flow = in_amount * r2["percent_area"]
            result.append({
                "cell_id": r1["cell_id"],
                "neighbor_id": r2["cell_id"],
                "in_amount" : flow
            })
        
# Convert results to a plain CSV (no geometry)
if len(result) == 0:
    print("No flows generated.")
else:
    df_res = pd.DataFrame(result)
    out_path = "all_flow_cell33.csv"
    df_res.to_csv(out_path, index=False)
    print(f"Wrote {out_path} with {len(df_res)} records")