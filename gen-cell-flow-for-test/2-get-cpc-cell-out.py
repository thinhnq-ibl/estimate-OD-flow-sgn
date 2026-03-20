import geopandas as gpd
import pandas as pd
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Loading data...")
# Read the shapes (subzones) and the grid of cells once
trips = pd.read_csv(os.path.join(base_dir, '../share_data/aggregated_trips.csv'))

all_cell = gpd.read_file(os.path.join(base_dir, "all_bounded_in_cells.geojson"))

# Load POI data to extract population and destination mass
pois = gpd.read_file(os.path.join(base_dir, '../share_data/detail_pois.geojson'))
pois['pop_count'] = pd.to_numeric(pois['pop_count'], errors='coerce').fillna(0)

# Calculate destination mass identical to the model's logic
poi_sum = pd.to_numeric(pois['tourism'], errors='coerce').fillna(0) + \
          pd.to_numeric(pois['office'], errors='coerce').fillna(0) + \
          pd.to_numeric(pois['shop'], errors='coerce').fillna(0) + \
          pd.to_numeric(pois['amenity'], errors='coerce').fillna(0) + \
          pd.to_numeric(pois['public_transport'], errors='coerce').fillna(0)

pois['mass'] = poi_sum

# Fast dictionary lookup map
poi_lookup = pois.set_index('cell_id')[['pop_count', 'mass']].to_dict('index')

# keep only relevant columns but preserve the geometry column so the result stays a
# GeoDataFrame (needed for GeoPandas methods like `to_file`).
result = []

print("Distributing trips by Population and POI density...")
for _, row in trips.iterrows():
    # 1. ORIGIN DOWNSCALING (by pop_count * area fraction)
    all_sub_cell = all_cell[all_cell["SUBZONE_C"] == row["ORIGIN_SUBZONE"]].copy()
    if all_sub_cell.empty:
        continue
        
    all_sub_cell['pop'] = all_sub_cell['cell_id'].map(lambda x: poi_lookup.get(x, {}).get('pop_count', 0))
    all_sub_cell['weight'] = all_sub_cell['intersect_area_m2'] 
    sum_weight = all_sub_cell['weight'].sum()
    
    if sum_weight == 0:
        # Fallback back to Area if population is exactly 0 everywhere in this subzone
        sum_weight = all_sub_cell['intersect_area_m2'].sum()
        all_sub_cell['percent_weight'] = all_sub_cell['intersect_area_m2'] / sum_weight if sum_weight > 0 else 0
    else:
        all_sub_cell['percent_weight'] = all_sub_cell['weight'] / sum_weight
        
    all_sub_cell['in_amount'] = all_sub_cell['percent_weight'] * row["COUNT"]

    # 2. DESTINATION DOWNSCALING (by mass * area fraction)
    all_sub_out_cell = all_cell[all_cell["SUBZONE_C"] == row["DESTINATION_SUBZONE"]].copy()
    if all_sub_out_cell.empty:
        continue
        
    all_sub_out_cell['mass'] = all_sub_out_cell['cell_id'].map(lambda x: poi_lookup.get(x, {}).get('mass', 0))
    all_sub_out_cell['weight_out'] = all_sub_out_cell['intersect_area_m2'] * all_sub_out_cell['mass']
    sum_weight_out = all_sub_out_cell['weight_out'].sum()
    
    if sum_weight_out == 0:
        # Fallback back to Area if POI Mass is exactly 0 everywhere in this subzone
        sum_weight_out = all_sub_out_cell['intersect_area_m2'].sum()
        all_sub_out_cell['percent_weight_out'] = all_sub_out_cell['intersect_area_m2'] / sum_weight_out if sum_weight_out > 0 else 0
    else:
        all_sub_out_cell['percent_weight_out'] = all_sub_out_cell['weight_out'] / sum_weight_out

    # 3. CONSTRUCT OD FLOWS
    for _, r1 in all_sub_cell.iterrows():
        in_amount = r1["in_amount"]
        if pd.isna(in_amount) or in_amount == 0:
            continue
            
        for _, r2 in all_sub_out_cell.iterrows():
            percent_out = r2["percent_weight_out"]
            if pd.isna(percent_out) or percent_out == 0:
                continue
                
            flow = in_amount * percent_out
            if flow > 0:
                result.append({
                    "cell_id": r1["cell_id"],
                    "neighbor_id": r2["cell_id"],
                    "in_amount" : flow
                })

print("Writing outputs...")
# Convert results to a plain CSV (no geometry)
if len(result) == 0:
    print("No flows generated.")
else:
    df_res = pd.DataFrame(result)
    out_path = "all_flow_cell33.csv"
    # Aggregate again just in case there are duplicated row generations
    df_res = df_res.groupby(['cell_id', 'neighbor_id'], as_index=False)['in_amount'].sum()
    df_res.to_csv(out_path, index=False)
    print(f"Wrote {out_path} with {len(df_res)} records")