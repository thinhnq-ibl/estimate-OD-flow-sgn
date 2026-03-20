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
    return float(row["tourism"]) + float(row["office"])  +  float(row["shop"])  + float(row["amenity"])  + float(row["public_transport"]) 

# Add mass to out_data and create a fast lookup
out_data['mass'] = out_data.apply(calculate_mass, axis=1)
poi_lookup = out_data.set_index('cell_id')['mass'].to_dict()
prob_lookup = out_data.set_index('cell_id')[['prob_0', 'prob_10']].to_dict('index')

# radiation formula helper (xi will be bound later)
def compute_radiation(xi, xj, sij):
    denominator = (xi + sij) * (xi + xj + sij)
    return (xi * xj) / denominator if denominator > 0 else 0

# 3. Process by Origin Cell
final_probs = []

for index, row in out_data.iterrows():
    # print(index, row)
    cell_id = row["cell_id"]
    # print("cell_id", cell_id)
    
    xi = poi_lookup[cell_id]
    p0 = prob_lookup[cell_id]['prob_0']
    # print(p0)
    
    # Filter for under_1km category
    under_1km = pair_cell_gdf[(pair_cell_gdf['category'] == "under_1km") & (pair_cell_gdf['cell_id'] == cell_id)].copy()
    all_group_under_1km =[]
    if not under_1km.empty:
        for ix, rw in under_1km.iterrows():
            p_ij = p0/(under_1km["cell_id"].count())
            final_probs.append([cell_id,rw["neighbor_id"],p_ij])

    # print(final_probs)
    p10 = prob_lookup[cell_id]['prob_10']
    # Filter for 1km-10km category
    group_1km_10km = pair_cell_gdf[(pair_cell_gdf['category'] == "1km-10km") & (pair_cell_gdf['cell_id'] == cell_id)].copy()
    
    all_group_1km_10km =[]
    # print(group_1km_10km["cell_id"].count())
    if not group_1km_10km.empty: 
    
        # Sort by distance to calculate s_ij cumulatively (Efficiency trick!)
        group_1km_10km = group_1km_10km.sort_values('distance_m')

        for ix, rw in group_1km_10km.iterrows():
            distance = rw["distance_m"]
            all_neigbor = group_1km_10km[group_1km_10km["distance_m"] < distance]
            all_neigbor['neighbor_mass'] = all_neigbor['neighbor_id'].map(poi_lookup).fillna(0)
            s_ij = all_neigbor['neighbor_mass'].sum()
            raw_Aij = compute_radiation(xi, poi_lookup[rw["neighbor_id"]], s_ij)
            all_group_1km_10km.append([cell_id,rw["neighbor_id"],raw_Aij])
        
        sum_Aij = 0

        for rw in all_group_1km_10km:
            sum_Aij += rw[2]
            
        if sum_Aij > 0:
            for rw in all_group_1km_10km:
                prob = (0.95 *(rw[2] / sum_Aij)+ 0.05/(group_1km_10km["cell_id"].count() )) * p10
                final_probs.append([rw[0], rw[1], prob])
    # print(final_probs)
    over_p10 = 1 - (prob_lookup[cell_id]['prob_10'] + prob_lookup[cell_id]['prob_0'])
    
    # Filter for 10km-20km category
    group_over_10km = pair_cell_gdf[(pair_cell_gdf['category'] == "10km-20km") & (pair_cell_gdf['cell_id'] == cell_id) & (pair_cell_gdf['neighbor_id']!= cell_id)].copy()
    # print(group_over_10km["cell_id"].count())
    all_group_over_10km =[]
    if not group_over_10km.empty:
        for ix, rw in group_over_10km.iterrows():
            distance = rw["distance_m"]
            all_neigbor = group_over_10km[group_over_10km["distance_m"] < distance]
            all_neigbor['neighbor_mass'] = all_neigbor['neighbor_id'].map(poi_lookup).fillna(0)
            s_ij = all_neigbor['neighbor_mass'].sum()
            raw_Aij = compute_radiation(xi, poi_lookup[rw["neighbor_id"]], s_ij)
            all_group_over_10km.append([cell_id,rw["neighbor_id"],raw_Aij])
        
        sum_Aij = 0

        for rw in all_group_over_10km:
            sum_Aij += rw[2]
            
        if sum_Aij > 0:
            for rw in all_group_over_10km:
                prob = (0.95 *(rw[2] / sum_Aij)+ 0.05/(group_over_10km["cell_id"].count() )) * over_p10
                final_probs.append([rw[0], rw[1], prob])
                
# 4. Merge results back to original dataframe

# print(final_probs)

results_df = pd.DataFrame(final_probs, columns=['cell_id','neighbor_id','in_prob'])
# pair_cell_gdf = pair_cell_gdf.merge(results_df, on=['cell_id', 'neighbor_id'], how='left', suffixes=('', '_new'))

results_df.to_csv(os.path.join(base_dir, "categorized_cell_pairs_radiation.csv"), index=False)