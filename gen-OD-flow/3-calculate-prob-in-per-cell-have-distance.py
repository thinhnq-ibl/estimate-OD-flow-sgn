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

# Distance-sensitive POI weights
under_1km_weights = {'tourism': 0.5, 'office': 1.0, 'shop': 2.0, 'amenity': 1.5, 'public_transport': 3.0}
km_1_10_weights = {'tourism': 1.0, 'office': 2.0, 'shop': 1.5, 'amenity': 1.0, 'public_transport': 1.5}
km_10_100_weights = {'tourism': 2.0, 'office': 1.5, 'shop': 1.0, 'amenity': 0.5, 'public_transport': 1.0}

def calculate_mass(row):
    def compute_poi_sum(weights):
        return (weights['tourism'] * float(row.get("tourism", 0)) + 
                weights['office'] * float(row.get("office", 0)) + 
                weights['shop'] * float(row.get("shop", 0)) + 
                weights['amenity'] * float(row.get("amenity", 0)) + 
                weights['public_transport'] * float(row.get("public_transport", 0)))
    
    pop_count = float(row.get("pop_count", 0))
    base_mass = math.log1p(pop_count)
    
    return {
        'under_1km': compute_poi_sum(under_1km_weights) + base_mass,
        '1km-10km': compute_poi_sum(km_1_10_weights) + base_mass,
        '10km-100km': compute_poi_sum(km_10_100_weights) + base_mass
    }

# Create lookup dict of dicts
poi_lookup = {row['cell_id']: calculate_mass(row) for _, row in out_data.iterrows()}

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
pair_cell_gdf['neighbor_mass'] = pair_cell_gdf.apply(lambda r: poi_lookup.get(r['neighbor_id'], {}).get(r['category'], 0), axis=1)

# radiation formula helper (xi will be bound later)
def compute_radiation(xi, xj, sij):
    denominator = (xi + sij) * (xi + xj + sij)
    return (xi * xj) / denominator if denominator > 0 else 0

# 3. Process by Origin Cell
final_probs = []

print("Running fast radiation model O(N)...")
for index, row in out_data.iterrows():
    cell_id = row["cell_id"]
    
    # xi will be set per category
    
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
    
    # Filter for under_1km category
    under_1km = cell_neighbors[cell_neighbors['category'] == "under_1km"]
    if not under_1km.empty:
        xi = poi_lookup[cell_id]['under_1km']
        under_1km = under_1km.copy()
        under_1km['raw_Aij'] = under_1km.apply(lambda rw: compute_radiation(xi, rw['neighbor_mass'], rw['s_ij']), axis=1)
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
        xi = poi_lookup[cell_id]['1km-10km']
        group_1km_10km = group_1km_10km.copy()
        group_1km_10km['raw_Aij'] = group_1km_10km.apply(lambda rw: compute_radiation(xi, rw['neighbor_mass'], rw['s_ij']), axis=1)
        sum_Aij = group_1km_10km['raw_Aij'].sum()
        if sum_Aij > 0:
            for ix, rw in group_1km_10km.iterrows():
                prob = (rw['raw_Aij'] / sum_Aij) * p10
                final_probs.append([cell_id, rw["neighbor_id"], prob])
                
    # Filter for 10km-100km category
    group_over_10km = cell_neighbors[(cell_neighbors['category'] == "10km-100km") & (cell_neighbors['neighbor_id'] != cell_id)]
    if not group_over_10km.empty:
        xi = poi_lookup[cell_id]['10km-100km']
        group_over_10km = group_over_10km.copy()
        group_over_10km['raw_Aij'] = group_over_10km.apply(lambda rw: compute_radiation(xi, rw['neighbor_mass'], rw['s_ij']), axis=1)
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