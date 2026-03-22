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

print("Preparing uniform weights...")
# Since each cell is exactly the same size in the grid (by definition of a regular grid), 
# distributing uniformly by area means giving each cell in the subzone equal weight. 
subzone_cell_area = all_cell.groupby('SUBZONE_C')['intersection_area'].transform('sum')

# Fallback to avoid divide-by-zero if a subzone has exactly 0 cells (it shouldn't in 'inner' merge)
all_cell['o_weight'] = np.where(subzone_cell_area > 0, all_cell['intersection_area'] / subzone_cell_area, 0)
all_cell['d_weight'] = np.where(subzone_cell_area > 0, all_cell['intersection_area'] / subzone_cell_area, 0)

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
                'destination_cell_id': d_row['cell_id'],
                'flow_count': flow_count
            })


out_path = "all_flow_cell33.csv"
data = pd.DataFrame(final_flow)
print(data['flow_count'].sum())
data.to_csv(out_path, index=False)
print(f"Wrote {out_path} with {len(final_flow)} records")
