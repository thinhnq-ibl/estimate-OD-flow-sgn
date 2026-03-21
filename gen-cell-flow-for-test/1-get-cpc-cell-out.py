import geopandas as gpd
import pandas as pd
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Loading data...")
# Read the shapes (subzones) and the grid of cells once
trips = pd.read_csv(os.path.join(base_dir, '../map/data_trip_sum.csv'))

all_cell = gpd.read_file(os.path.join(base_dir, "../subzone-cell/final_pois_2.geojson"))

print("Preparing POI-based weights...")
# Distribute the subzone ground truth trips according to specific POI densities per cell 
# This matches real-world concentration and aligns with the engine's Radiation model expectations!

poi_cols = ['tourism', 'office', 'shop', 'amenity', 'public_transport']
mass = 0 #
for col in poi_cols:
    if col in all_cell.columns:
        mass += pd.to_numeric(all_cell[col], errors='coerce').fillna(0)

if 'pop_count' in all_cell.columns:
    pop = pd.to_numeric(all_cell['pop_count'], errors='coerce').fillna(0)
    mass += np.log1p(pop)

all_cell['mass'] = mass
subzone_mass = all_cell.groupby('SUBZONE_C')['mass'].transform('sum')

# Calculate explicit feature proportion instead of division by simple geometric grid counts
all_cell['o_weight'] = np.where(subzone_mass > 0, all_cell['mass'] / subzone_mass, 0)
all_cell['d_weight'] = np.where(subzone_mass > 0, all_cell['mass'] / subzone_mass, 0)

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
