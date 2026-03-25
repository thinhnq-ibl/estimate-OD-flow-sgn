import math
import os
import pandas as pd
import geopandas as gpd
import numpy as np

# 1. Load Data
# ensure we read files relative to this script's directory so it works when
# launched from the project root or any other cwd
base_dir = os.path.dirname(os.path.abspath(__file__))
out_data = gpd.read_file(os.path.join(base_dir, "../zone/pop_grid.geojson"))
pair_cell_gdf = pd.read_csv(os.path.join(base_dir, "categorized_cell_pairs.csv"))
district_map = pd.read_csv(os.path.join(base_dir, '../map/district_zone.csv'))
landuse_data = gpd.read_file(os.path.join(base_dir, "../zone/detail_landuse.geojson"))

# CONFIGURATION: POI WEIGHTS
# Tuning these weights is critical for improving CPC.
# Suggestion: Use an optimization algorithm to find the best weights that match Ground Truth flow.

POI_WEIGHTS = {
    'office': 15,
    'public_transport': 50,
    'shop': 10,
    'amenity': 2,
    'tourism': 4,
    'leisure': 1
}

#map cell to district for probability lookup
out_data = out_data.merge(district_map, left_on='SUBZONE_C', right_on='zone_id', how='left')
out_data['district_id'] = out_data['district_id'].fillna(-1)  # Handle cells without a district mapping

# ORIGIN MASS: Động lực sinh ra chuyến đi là DÂN SỐ (Population)
# VECTORIZED OPTIMIZATION: Replaced .apply() with vectorized operations for speed
out_data['origin_mass'] = out_data['population'].fillna(0) + 1.0

# Calculate masses for ALL cells to ensure global lookup coverage
# Calculate Destination Mass using vectorized weighted sum
# Initialize with 1.0 base mass
out_data['dest_mass'] = 1.0
for col, weight in POI_WEIGHTS.items():
    if col in out_data.columns:
        out_data['dest_mass'] += out_data[col].fillna(0) * weight
    else:
        print(f"Warning: POI column '{col}' not found in data.")

# Fix Lookup: Sử dụng cell_id đơn nhất làm key để map() hoạt động chính xác
unique_cells = out_data.drop_duplicates(subset=['SUBZONE_C']).copy()
origin_lookup = unique_cells.set_index('SUBZONE_C')['origin_mass'].to_dict()
dest_lookup = unique_cells.set_index('SUBZONE_C')['dest_mass'].to_dict()

district_prob_lookup = {}
ob = 1
if ob == 1:
    prob_data = pd.read_csv(os.path.join(base_dir, "../check-data-distribution/gt_prob.csv"))

    # Clean category column once to ensure consistent lookup
    prob_data['clean_category'] = prob_data['category'].astype(str).str.replace(' ', '')

    for district, group in prob_data.groupby('district_id'):
        try:
            p0 = float(group[group['category'] == '0']['p_gt'].iloc[0])
        except IndexError:
            print(f"No p0 found for district {district}")
            p0 = 0.0
            
        try:
            # Match '(0,10)' via stripped strings
            p10 = float(group[group['clean_category'] == '(0,10)']['p_gt'].iloc[0])
        except IndexError:
            print(f"No p10 found for district {district}")
            p10 = 0.0
            
        district_prob_lookup[district] = {'prob_0': p0, 'prob_10': p10}
else:
    prob_data = pd.read_csv(os.path.join(base_dir, "../check-data-distribution/fb_agg.csv"))

    # Clean category column once to ensure consistent lookup
    prob_data['clean_category'] = prob_data['category'].astype(str).str.replace(' ', '')

    district_prob_lookup = {}
    for district, group in prob_data.groupby('district_id'):
        try:
            p0 = float(group[group['category'] == '0']['p_fb'].iloc[0])
        except IndexError:
            print(f"No p0 found for district {district}")
            p0 = 0.0
            
        try:
            # Match '(0,10)' via stripped strings
            p10 = float(group[group['clean_category'] == '(0,10)']['p_fb'].iloc[0])
        except IndexError:
            print(f"No p10 found for district {district}")
            p10 = 0.0
            
        district_prob_lookup[district] = {'prob_0': p0, 'prob_10': p10}


prob_lookup = {}
for _, row in out_data.iterrows():
    prob_lookup[row['SUBZONE_C']] = district_prob_lookup.get(row.get('district_id'), {'prob_0': 0.0, 'prob_10': 0.0})

# Precompute neighbor destination masses globally for extreme speed 
pair_cell_gdf['neighbor_mass'] = pair_cell_gdf['neighbor_subzone_id'].map(dest_lookup).fillna(0)

# OPTIMIZATION: Sort globally once to avoid sorting inside the loop
pair_cell_gdf.sort_values(by=['subzone_id', 'distance_m'], inplace=True)

# print(pair_cell_gdf.head())

# radiation formula helper (xi will be bound later)
def compute_radiation(xi, xj, sij, first_cell_mass):
    sij = max(sij - first_cell_mass, 0)  # Ensure s_ij doesn't include the first neighbor's mass
    denominator = (xi + sij) * (xi + xj + sij)
    return (xi * xj) / denominator if denominator > 0 else 0

# 3. Process by Origin Cell
final_probs = []

# Group pairs by origin for O(1) access inside loop
pair_grouped = pair_cell_gdf.groupby('subzone_id')

print("Running fast radiation model O(N)...")

for index, row in out_data.iterrows():
    subzone_id = row["SUBZONE_C"]
    
    xi = origin_lookup.get(subzone_id, 0)
    
    # Skip if cell missing probabilities
    if subzone_id not in prob_lookup:
        print(f"No prob found for cell {subzone_id}, skipping.")
        continue
        
    p0 = prob_lookup[subzone_id]['prob_0']
    p10 = prob_lookup[subzone_id]['prob_10']
    over_p10 = 1 - (p10 + p0)
    
    # ⚡ [TỐI ƯU SIÊU NHANH] Use groupby object instead of filtering df
    try:
        cell_neighbors = pair_grouped.get_group(subzone_id).copy()  # Get neighbors for this origin cell
        # print(f"Processing cell {subzone_id} with {len(cell_neighbors)} neighbors...")
    except KeyError:
        print(f"No neighbors found for cell {subzone_id}")
        cell_neighbors = pd.DataFrame()
    
    if cell_neighbors.empty:
        print(f"No neighbors found for cell {subzone_id}")
        continue
        
    # s_ij is total mass strictly closer. Use groupby sum then cumsum then shift.
    ring_mass = cell_neighbors.groupby('distance_m')['neighbor_mass'].sum().cumsum().shift(fill_value=0)
    cell_neighbors['s_ij'] = cell_neighbors['distance_m'].map(ring_mass)

    first_cell = cell_neighbors.iloc[0]['neighbor_mass']
    
    # Calculate pre-normalized radiation attraction A_ij for all neighbors
    # OPTIMIZATION: Vectorize calculation instead of .apply()
    s_ij_adj = np.maximum(cell_neighbors['s_ij'] - first_cell, 0)
    denom = (xi + s_ij_adj) * (xi + cell_neighbors['neighbor_mass'] + s_ij_adj)
    cell_neighbors['raw_Aij'] = np.where(denom > 0, (xi * cell_neighbors['neighbor_mass']) / denom, 0)
    
    # Identify groups
    under_1km = cell_neighbors[cell_neighbors['category'] == "under_1km"]
    group_1km_10km = cell_neighbors[cell_neighbors['category'] == "1km-10km"]
    group_over_10km = cell_neighbors[(cell_neighbors['category'] == "10km-100km")]
    
    # Check availability
    has_under = not under_1km.empty
    has_1_10 = not group_1km_10km.empty
    has_over = not group_over_10km.empty
    
    # Normalization: If a category is missing, redistribute its weight to others
    w_under = p0 if has_under else 0.0
    w_1_10 = p10 if has_1_10 else 0.0
    w_over = over_p10 if has_over else 0.0
    
    total_w = w_under + w_1_10 + w_over
    
    if total_w <= 0:
        continue
        
    p0_adj = w_under / total_w
    p10_adj = w_1_10 / total_w
    over_p10_adj = w_over / total_w
    # print(under_1km)
    # Filter for under_1km category
    if has_under:
        sum_Aij = under_1km['raw_Aij'].sum()
        if sum_Aij <= 0:
            sum_Aij = 0 # trigger uniform

        for _, rw in under_1km.iterrows():
            # FIX: Standard normalization: (val / sum) * total_prob
            prob = (rw['raw_Aij'] / sum_Aij * p0_adj) if sum_Aij > 0 else (p0_adj / len(under_1km))
            final_probs.append([subzone_id, rw["neighbor_subzone_id"], prob])

    # Filter for 1km-10km category
    if has_1_10: 
        sum_Aij = group_1km_10km['raw_Aij'].sum()
        # Use uniform if radiation attraction is 0 (fallback)
        if sum_Aij <= 0:
            sum_Aij = 0 # trigger uniform
            
        for _, rw in group_1km_10km.iterrows():
            prob = (rw['raw_Aij'] / sum_Aij * p10_adj) if sum_Aij > 0 else (p10_adj / len(group_1km_10km))
            final_probs.append([subzone_id, rw["neighbor_subzone_id"], prob])
                
    # Filter for 10km-100km category
    if has_over:
        sum_Aij = group_over_10km['raw_Aij'].sum()
        if sum_Aij <= 0:
            sum_Aij = 0
            
        for _, rw in group_over_10km.iterrows():
            prob = (rw['raw_Aij'] / sum_Aij * over_p10_adj) if sum_Aij > 0 else (over_p10_adj / len(group_over_10km))
            final_probs.append([subzone_id, rw["neighbor_subzone_id"], prob])
    
# 4. Merge results back to original dataframe

results_df = pd.DataFrame(final_probs, columns=['subzone_id','neighbor_subzone_id','in_prob'])
out_path = os.path.join(base_dir, "categorized_cell_pairs_radiation.csv")
results_df.to_csv(out_path, index=False)
print("Finished writing to", out_path)