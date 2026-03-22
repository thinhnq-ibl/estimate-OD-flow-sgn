import geopandas as gpd
import pandas as pd
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Loading data...")
# Read the shapes (subzones) and the grid of cells once
trips = pd.read_csv(os.path.join(base_dir, '../map/data_trip_sum.csv'))

print(trips['COUNT'].sum())
all_cell = gpd.read_file(os.path.join(base_dir, "../subzone-cell/detail_pois_district.geojson"))

print("Preparing weights based on Population (Origin) and POIs (Destination)...")

# Fill NaNs for safety
for col in ['pop_count', 'office', 'public_transport', 'shop', 'amenity', 'tourism', 'leisure']:
    if col in all_cell.columns:
        all_cell[col] = pd.to_numeric(all_cell[col], errors='coerce').fillna(0)
    else:
        all_cell[col] = 0

# Calculate Origin Score (Population-based)
all_cell['o_score'] = all_cell['pop_count']

# Calculate Destination Score (POI-based)
# Strong attraction to Work/Transport hubs
all_cell['d_score'] = (
    all_cell['office'] * 15 + 
    all_cell['public_transport'] * 10 + 
    all_cell['shop'] * 5 + 
    all_cell['amenity'] * 1 + 
    all_cell['tourism'] * 1 + 
    all_cell['leisure'] * 1
)

def calculate_weights(df, score_col, area_col='intersection_area', group_col='SUBZONE_C'):
    sum_score = df.groupby(group_col)[score_col].transform('sum')
    sum_area = df.groupby(group_col)[area_col].transform('sum')
    
    # Avoid division by zero warnings
    with np.errstate(divide='ignore', invalid='ignore'):
        score_weight = df[score_col] / sum_score
        area_weight = df[area_col] / sum_area
        
    # Use score weight if sum_score > 0, else fallback to area weight
    return np.where(sum_score > 0, score_weight.fillna(0), 
                    np.where(sum_area > 0, area_weight.fillna(0), 0))

all_cell['o_weight'] = calculate_weights(all_cell, 'o_score')
all_cell['d_weight'] = calculate_weights(all_cell, 'd_score')

print("Distributing trips...")
final_flow = []
for _, row in trips.iterrows():
    origin_subzone = row['ORIGIN_SUBZONE']
    destination_subzone = row['DESTINATION_SUBZONE']
    count = row['COUNT']
    
    # Get cells in origin and destination subzones
    origin_cells = all_cell[all_cell['SUBZONE_C'] == origin_subzone]
    destination_cells = all_cell[all_cell['SUBZONE_C'] == destination_subzone]
    
    # If either subzone has no cells, skip this trip (or handle as needed)
    if origin_cells.empty or destination_cells.empty:
        print(origin_subzone, destination_subzone)
        continue
    
    # Distribute count to cell pairs
    for _, o_row in origin_cells.iterrows():
        for _, d_row in destination_cells.iterrows():
            flow_count = count * o_row['o_weight'] * d_row['d_weight']
            final_flow.append({
                'origin_cell_id': o_row['cell_id'],
                'origin_subzone_id': o_row['SUBZONE_C'],
                'destination_cell_id': d_row['cell_id'],
                'destination_subzone_id': d_row['SUBZONE_C'],
                'flow_count': flow_count
            })


out_path = "all_flow_cell_with_subzone.csv"
data = pd.DataFrame(final_flow)
print(data['flow_count'].sum())
data.to_csv(out_path, index=False)
print(f"Wrote {out_path} with {len(final_flow)} records")
