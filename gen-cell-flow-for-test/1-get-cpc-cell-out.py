import geopandas as gpd
import pandas as pd
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Loading data...")
# Read the shapes (subzones) and the grid of cells once
trips = pd.read_csv(os.path.join(base_dir, '../map/data_trip_sum.csv'))

all_cell = gpd.read_file(os.path.join(base_dir, "../subzone-cell/final_pois_2.geojson"))

print("Preparing uniform weights...")
# Since each cell is exactly the same size in the grid (by definition of a regular grid), 
# distributing uniformly by area means giving each cell in the subzone equal weight. 
subzone_cell_count = all_cell.groupby('SUBZONE_C')['cell_id'].transform('count')

# Fallback to avoid divide-by-zero if a subzone has exactly 0 cells (it shouldn't in 'inner' merge)
all_cell['o_weight'] = np.where(subzone_cell_count > 0, 1.0 / subzone_cell_count, 0)
all_cell['d_weight'] = np.where(subzone_cell_count > 0, 1.0 / subzone_cell_count, 0)

print("Distributing trips...")
# Merge trips with origin cells
trips_origin = trips.merge(
    all_cell[['SUBZONE_C', 'cell_id', 'o_weight']],
    left_on='ORIGIN_SUBZONE',
    right_on='SUBZONE_C',
    how='inner'
)
trips_origin.rename(columns={'cell_id': 'origin_cell_id'}, inplace=True)
trips_origin['origin_flow'] = trips_origin['COUNT'] * trips_origin['o_weight']

# Merge with destination cells
trips_full = trips_origin.merge(
    all_cell[['SUBZONE_C', 'cell_id', 'd_weight']],
    left_on='DESTINATION_SUBZONE',
    right_on='SUBZONE_C',
    how='inner'
)
trips_full.rename(columns={'cell_id': 'dest_cell_id'}, inplace=True)
trips_full['flow'] = trips_full['origin_flow'] * trips_full['d_weight']

# Filter out zero flows
final_flow = trips_full[trips_full['flow'] > 0][['origin_cell_id', 'dest_cell_id', 'flow']]

print(f"Aggregating {len(final_flow)} flows...")
# Aggregate again just in case there are duplicated row generations
final_flow = final_flow.groupby(['origin_cell_id', 'dest_cell_id'], as_index=False)['flow'].sum()
final_flow.rename(columns={'origin_cell_id': 'cell_id', 'dest_cell_id': 'neighbor_id', 'flow': 'in_amount'}, inplace=True)

out_path = "all_flow_cell33.csv"
final_flow.to_csv(out_path, index=False)
print(f"Wrote {out_path} with {len(final_flow)} records")
