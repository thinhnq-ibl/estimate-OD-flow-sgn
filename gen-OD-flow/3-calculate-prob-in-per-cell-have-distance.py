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
    poi_sum = float(row.get("tourism", 0)) + float(row.get("office", 0)) + float(row.get("shop", 0)) + float(row.get("amenity", 0)) + float(row.get("public_transport", 0))
    pop_count = float(row.get("pop_count", 0))
    # Sử dụng log1p (log cơ số tự nhiên cộng 1) để pop_count không chiếm ưu thế, nhưng vẫn tạo trọng số khi poi_sum = 0
    return poi_sum  

# Add mass to out_data and create a fast lookup
out_data['mass'] = out_data.apply(calculate_mass, axis=1)
poi_lookup = out_data.set_index('cell_id')['mass'].to_dict()
prob_lookup = out_data.set_index('cell_id')[['prob_0', 'prob_10']].to_dict('index')

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
    
    # ⚡ [TỐI ƯU SIÊU NHANH] Tách lấy toàn bộ neighbor của ĐÚNG cell_id này ra 1 data frame cực nhỏ (chỉ vài trăm/nghìn dòng). 
    # Việc filter (toán tử boolean) trên dataframe siêu nhỏ sẽ chạy chưa tới 0.001 giây, thay vì quét cả triệu dòng của file tổng!
    cell_neighbors = pair_cell_gdf[pair_cell_gdf['cell_id'] == cell_id]
    
    if cell_neighbors.empty:
        continue
        
    # Filter for under_1km category
    under_1km = cell_neighbors[cell_neighbors['category'] == "under_1km"]
    if not under_1km.empty:
        count_0 = len(under_1km)
        for ix, rw in under_1km.iterrows():
            p_ij = p0 / count_0
            final_probs.append([cell_id, rw["neighbor_id"], p_ij])

    # Filter for 1km-10km category
    group_1km_10km = cell_neighbors[cell_neighbors['category'] == "1km-10km"]
    all_group_1km_10km = []
    if not group_1km_10km.empty: 
        # Scan over local ring ONLY (Not from center 0km)
        for ix, rw in group_1km_10km.iterrows():
            distance = rw["distance_m"]
            s_ij = group_1km_10km.loc[group_1km_10km["distance_m"] < distance, 'neighbor_mass'].sum()
            raw_Aij = compute_radiation(xi, rw["neighbor_mass"], s_ij)
            all_group_1km_10km.append([cell_id, rw["neighbor_id"], raw_Aij])
        
        sum_Aij = sum(rw[2] for rw in all_group_1km_10km)
        
        count_10 = len(group_1km_10km)
        if sum_Aij > 0:
            for rw in all_group_1km_10km:
                prob = (rw[2] / sum_Aij) * p10
                final_probs.append([rw[0], rw[1], prob])
                
    # Filter for 10km-20km category
    group_over_10km = cell_neighbors[(cell_neighbors['category'] == "10km-20km") & (cell_neighbors['neighbor_id'] != cell_id)]
    all_group_over_10km = []
    if not group_over_10km.empty:
        # Scan over local ring ONLY (Not from center 0km)
        for ix, rw in group_over_10km.iterrows():
            distance = rw["distance_m"]
            s_ij = group_over_10km.loc[group_over_10km["distance_m"] < distance, 'neighbor_mass'].sum()
            raw_Aij = compute_radiation(xi, rw["neighbor_mass"], s_ij)
            all_group_over_10km.append([cell_id, rw["neighbor_id"], raw_Aij])
        
        sum_Aij = sum(rw[2] for rw in all_group_over_10km)
        
        count_over = len(group_over_10km)
        if sum_Aij > 0:
            for rw in all_group_over_10km:
                prob = (rw[2] / sum_Aij) * over_p10
                final_probs.append([rw[0], rw[1], prob])
                
# 4. Merge results back to original dataframe

results_df = pd.DataFrame(final_probs, columns=['cell_id','neighbor_id','in_prob'])
out_path = os.path.join(base_dir, "categorized_cell_pairs_radiation.csv")
results_df.to_csv(out_path, index=False)
print("Finished writing to", out_path)