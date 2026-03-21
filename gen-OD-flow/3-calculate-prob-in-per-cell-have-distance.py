import math
import os
import pandas as pd
import geopandas as gpd

# 1. Load Data
# ensure we read files relative to this script's directory so it works when
# launched from the project root or any other cwd
base_dir = os.path.dirname(os.path.abspath(__file__))
out_data = gpd.read_file(os.path.join(base_dir, "final_summed_out_cells.geojson"))
pair_cell_gdf = pd.read_csv(os.path.join(base_dir, "categorized_cell_pairs.csv"))

def calculate_mass(row):
    # Apply further adjusted weights: tourism(0.2), office(1.8), shop(1.4), amenity(0.4), public_transport(2.5)
    poi_sum = (0.2 * float(row.get("tourism", 0)) + 
               1.8 * float(row.get("office", 0)) + 
               1.4 * float(row.get("shop", 0)) + 
               0.4 * float(row.get("amenity", 0)) + 
               2.5 * float(row.get("public_transport", 0)))
    pop_count = float(row.get("pop_count", 0))
    # Sử dụng log1p (log cơ số tự nhiên cộng 1) để pop_count không chiếm ưu thế, nhưng vẫn tạo trọng số khi poi_sum = 0
    return poi_sum + math.log1p(pop_count) # +1.0 laplace smoothing matching ground truth

# Add mass to out_data and create a fast lookup
out_data['mass'] = out_data.apply(calculate_mass, axis=1)
poi_lookup = out_data.set_index('cell_id')['mass'].to_dict()

prob_data = pd.read_csv(os.path.join(base_dir, "../check-data-distribution/gt_prob.csv"))

# prob_lookup find prob_0 and prob_10 from prob_data category: 0 , (0,10) for each cell_id
district_prob_lookup = {}
for district, group in prob_data.groupby('district_id'):
    try:
        p0 = float(group[group['category'] == '0']['p_gt'].iloc[0])
    except IndexError:
        p0 = 0.0
        
    try:
        # Match '(0, 10)' or '(0,10)' via stripped strings to be safe
        p10 = float(group[group['category'].str.replace(' ', '') == '(0,10)']['p_gt'].iloc[0])
    except IndexError:
        p10 = 0.0
        
    district_prob_lookup[district] = {'prob_0': p0, 'prob_10': p10}

prob_lookup = {}
for _, row in out_data.iterrows():
    prob_lookup[row['cell_id']] = district_prob_lookup.get(row.get('district_id'), {'prob_0': 0.0, 'prob_10': 0.0})


# Precompute neighbor masses globally for extreme speed 
pair_cell_gdf['neighbor_mass'] = pair_cell_gdf['neighbor_id'].map(poi_lookup).fillna(0)

# radiation formula helper (xi will be bound later)
def compute_radiation(xi, xj, sij):
    denominator = (xi + sij) * (xi + xj + sij)
    return (xi * xj) / denominator if denominator > 0 else 0

# 3. Process by Origin Cell
final_probs = []

print("Running fast radiation model O(N)...")
for index, row in out_data.iterrows():
    cell_id = row["cell_id"]
    
    xi = poi_lookup.get(cell_id, 0)
    
    # Skip if cell missing probabilities
    if cell_id not in prob_lookup:
        continue
        
    p0 = prob_lookup[cell_id]['prob_0']
    p10 = prob_lookup[cell_id]['prob_10']
    over_p10 = 1 - (p10 + p0)
    
    # ⚡ [TỐI ƯU SIÊU NHANH] Tách lấy toàn bộ neighbor của ĐÚNG cell_id này ra 1 data frame cực nhỏ.
    cell_neighbors = pair_cell_gdf[pair_cell_gdf['cell_id'] == cell_id].copy()
    
    if cell_neighbors.empty:
        continue
        
    # Sort by distance correctly and compute EXACT s_ij across all rings
    cell_neighbors = cell_neighbors.sort_values('distance_m')
    
    # s_ij is total mass strictly closer. Use groupby sum then cumsum then shift.
    ring_mass = cell_neighbors.groupby('distance_m')['neighbor_mass'].sum().cumsum().shift(fill_value=0)
    cell_neighbors['s_ij'] = cell_neighbors['distance_m'].map(ring_mass)
    
    # Calculate pre-normalized radiation attraction A_ij for all neighbors
    cell_neighbors['raw_Aij'] = cell_neighbors.apply(lambda rw: compute_radiation(xi, rw['neighbor_mass'], rw['s_ij']), axis=1)
    
    # Filter for under_1km category
    under_1km = cell_neighbors[cell_neighbors['category'] == "under_1km"]
    if not under_1km.empty:
        sum_Aij = under_1km['raw_Aij'].sum()
        if sum_Aij > 0:
            for ix, rw in under_1km.iterrows():
                p_ij = (rw['raw_Aij'] / sum_Aij) * p0
                final_probs.append([cell_id, rw["neighbor_id"], p_ij])
        else:
            count_0 = len(under_1km)
            for ix, rw in under_1km.iterrows():
                p_ij = p0 / count_0
                final_probs.append([cell_id, rw["neighbor_id"], p_ij])

    # Filter for 1km-10km category
    group_1km_10km = cell_neighbors[cell_neighbors['category'] == "1km-10km"]
    if not group_1km_10km.empty: 
        sum_Aij = group_1km_10km['raw_Aij'].sum()
        if sum_Aij > 0:
            for ix, rw in group_1km_10km.iterrows():
                prob = (rw['raw_Aij'] / sum_Aij) * p10
                final_probs.append([cell_id, rw["neighbor_id"], prob])
                
    # Filter for 10km-100km category
    group_over_10km = cell_neighbors[(cell_neighbors['category'] == "10km-100km") & (cell_neighbors['neighbor_id'] != cell_id)]
    if not group_over_10km.empty:
        sum_Aij = group_over_10km['raw_Aij'].sum()
        if sum_Aij > 0:
            for ix, rw in group_over_10km.iterrows():
                prob = (rw['raw_Aij'] / sum_Aij) * over_p10
                final_probs.append([cell_id, rw["neighbor_id"], prob])
                
# 4. Merge results back to original dataframe

results_df = pd.DataFrame(final_probs, columns=['cell_id','neighbor_id','in_prob'])
out_path = os.path.join(base_dir, "categorized_cell_pairs_radiation.csv")
results_df.to_csv(out_path, index=False)
print("Finished writing to", out_path)