import math
import os
import pandas as pd
import geopandas as gpd
import numpy as np

# 1. Load Data
# ensure we read files relative to this script's directory so it works when
# launched from the project root or any other cwd
base_dir = os.path.dirname(os.path.abspath(__file__))
out_data = gpd.read_file(os.path.join(base_dir, "final_summed_out_cells.geojson"))
# Load FULL cell data to ensure all destinations (even those without outflow) are known
all_cells = gpd.read_file(os.path.join(base_dir, "../subzone-cell/detail_pois_district.geojson"))
pair_cell_gdf = pd.read_csv(os.path.join(base_dir, "categorized_cell_pairs.csv"))

def calculate_origin_mass(row):
    # ORIGIN MASS: Động lực sinh ra chuyến đi là DÂN SỐ (Population)
    # Không dùng POI cho điểm đi (trừ khi là mô hình return trip)
    pop_count = float(row.get("pop_count", 0))
    # Cộng 1 để tránh log(0) hoặc chia cho 0
    return pop_count + 1.0

def calculate_dest_mass(row):
    # DESTINATION MASS: Động lực hút chuyến đi là POI (Văn phòng, Trường học, Trạm xe)
    office = float(row.get("office", 0))
    transport = float(row.get("public_transport", 0))
    shop = float(row.get("shop", 0))
    amenity = float(row.get("amenity", 0))
    tourism = float(row.get("tourism", 0))
    leisure = float(row.get("leisure", 0))
    
    # ALIGN WEIGHTS WITH GROUND TRUTH GENERATION (1-get-cpc-cell-out.py)
    # Office * 15, Transport * 10, Shop * 5, Others * 1
    # Cần tạo sự chênh lệch lớn để dòng chảy tập trung về các trung tâm
    weighted_sum = (office * 15.0) + (transport * 10.0) + (shop * 5.0) + (amenity * 1.0) + (tourism * 1.0) + (leisure * 1.0)
    return weighted_sum + 1.0

# Calculate masses for ALL cells to ensure global lookup coverage
all_cells['origin_mass'] = all_cells.apply(calculate_origin_mass, axis=1)
all_cells['dest_mass'] = all_cells.apply(calculate_dest_mass, axis=1)

# Fix Lookup: Sử dụng cell_id đơn nhất làm key để map() hoạt động chính xác
unique_cells = all_cells.drop_duplicates(subset=['cell_id'])
origin_lookup = unique_cells.set_index('cell_id')['origin_mass'].to_dict()
dest_lookup = unique_cells.set_index('cell_id')['dest_mass'].to_dict()

prob_data = pd.read_csv(os.path.join(base_dir, "../check-data-distribution/gt_prob.csv"))

# prob_lookup find prob_0 and prob_10 from prob_data category: 0 , (0,10) for each cell_id
district_prob_lookup = {}
for district, group in prob_data.groupby('district_id'):
    try:
        p0 = float(group[group['category'] == '0']['p_gt'].iloc[0])
    except IndexError:
        print(f"No p0 found for district {district}")
        p0 = 0.0
        
    try:
        # Match '(0, 10)' or '(0,10)' via stripped strings to be safe
        p10 = float(group[group['category'].str.replace(' ', '') == '(0,10)']['p_gt'].iloc[0])
    except IndexError:
        print(f"No p10 found for district {district}")
        p10 = 0.0
        
    district_prob_lookup[district] = {'prob_0': p0, 'prob_10': p10}

prob_lookup = {}
for _, row in out_data.iterrows():
    prob_lookup[row['cell_id'], row['zone_id']] = district_prob_lookup.get(row.get('district_id'), {'prob_0': 0.0, 'prob_10': 0.0})


# Precompute neighbor destination masses globally for extreme speed 
pair_cell_gdf['neighbor_mass'] = pair_cell_gdf['neighbor_id'].map(dest_lookup).fillna(0)

# radiation formula helper (xi will be bound later)
def compute_radiation(xi, xj, sij):
    denominator = (xi + sij) * (xi + xj + sij)
    return (xi * xj) / denominator if denominator > 0 else 0

# 3. Process by Origin Cell
final_probs = []

# Group pairs by origin for O(1) access inside loop
pair_grouped = pair_cell_gdf.groupby(['cell_id', 'subzone_id'])

print("Running fast radiation model O(N)...")

for index, row in out_data.iterrows():
    cell_id = row["cell_id"]
    subzone_id = row["zone_id"]
    
    xi = origin_lookup.get(cell_id, 0)
    
    # Skip if cell missing probabilities
    if (cell_id, subzone_id) not in prob_lookup:
        print(f"No prob found for cell {cell_id, subzone_id}, skipping.")
        continue
        
    p0 = prob_lookup[cell_id, subzone_id]['prob_0']
    p10 = prob_lookup[cell_id, subzone_id]['prob_10']
    over_p10 = 1 - (p10 + p0)
    
    # ⚡ [TỐI ƯU SIÊU NHANH] Use groupby object instead of filtering df
    try:
        cell_neighbors = pair_grouped.get_group((cell_id, subzone_id)).copy()
    except KeyError:
        cell_neighbors = pd.DataFrame()
    
    if cell_neighbors.empty:
        print(f"No neighbors found for cell {cell_id, subzone_id}")
        continue
        
    # Sort by distance correctly and compute EXACT s_ij across all rings
    cell_neighbors = cell_neighbors.sort_values('distance_m')
    
    # s_ij is total mass strictly closer. Use groupby sum then cumsum then shift.
    ring_mass = cell_neighbors.groupby('distance_m')['neighbor_mass'].sum().cumsum().shift(fill_value=0)
    cell_neighbors['s_ij'] = cell_neighbors['distance_m'].map(ring_mass)
    
    # Calculate pre-normalized radiation attraction A_ij for all neighbors
    cell_neighbors['raw_Aij'] = cell_neighbors.apply(lambda rw: compute_radiation(xi, rw['neighbor_mass'], rw['s_ij']), axis=1)
    
    # Identify groups
    under_1km = cell_neighbors[cell_neighbors['category'] == "under_1km"]
    group_1km_10km = cell_neighbors[cell_neighbors['category'] == "1km-10km"]
    group_over_10km = cell_neighbors[(cell_neighbors['category'] == "10km-100km") & (cell_neighbors['neighbor_id'] != cell_id)]
    
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
    
    # Filter for under_1km category
    if has_under:
        sum_Aij = under_1km['raw_Aij'].sum()
        if sum_Aij <= 0:
            sum_Aij = 0
            
        for _, rw in under_1km.iterrows():
            prob = (rw['raw_Aij'] / sum_Aij * p0_adj) if sum_Aij > 0 else (p0_adj / len(under_1km))
            final_probs.append([cell_id, subzone_id, rw["neighbor_id"], rw["neighbor_subzone_id"], prob])

    # Filter for 1km-10km category
    if has_1_10: 
        sum_Aij = group_1km_10km['raw_Aij'].sum()
        # Use uniform if radiation attraction is 0 (fallback)
        if sum_Aij <= 0:
            sum_Aij = 0 # trigger uniform
            
        for _, rw in group_1km_10km.iterrows():
            prob = (rw['raw_Aij'] / sum_Aij * p10_adj) if sum_Aij > 0 else (p10_adj / len(group_1km_10km))
            final_probs.append([cell_id, subzone_id, rw["neighbor_id"], rw["neighbor_subzone_id"], prob])
                
    # Filter for 10km-100km category
    if has_over:
        sum_Aij = group_over_10km['raw_Aij'].sum()
        if sum_Aij <= 0:
            sum_Aij = 0
            
        for _, rw in group_over_10km.iterrows():
            prob = (rw['raw_Aij'] / sum_Aij * over_p10_adj) if sum_Aij > 0 else (over_p10_adj / len(group_over_10km))
            final_probs.append([cell_id, subzone_id, rw["neighbor_id"], rw["neighbor_subzone_id"], prob])
                
# 4. Merge results back to original dataframe

results_df = pd.DataFrame(final_probs, columns=['cell_id','subzone_id','neighbor_id','neighbor_subzone_id','in_prob'])
out_path = os.path.join(base_dir, "categorized_cell_pairs_radiation.csv")
results_df.to_csv(out_path, index=False)
print("Finished writing to", out_path)