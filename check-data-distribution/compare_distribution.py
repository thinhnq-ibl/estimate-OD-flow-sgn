import pandas as pd
import numpy as np
from scipy.stats import entropy
import os
import geopandas as gpd
from shapely.geometry import Point

# --- 1. CONFIGURATION ---
base_dir = os.path.dirname(os.path.abspath(__file__))
gt_file = os.path.join(base_dir, '../map/data_sgp_pcm_trip.csv')
fb_file = os.path.join(base_dir, '../map/1922039342088483_2025-12-17.csv')
district_map_file = os.path.join(base_dir, '../map/district_zone.csv')

print("1. Loading Ground Truth Data and District mapping...")
gt_df = pd.read_csv(gt_file)
district_zone_df = pd.read_csv(district_map_file)

# Tạo cột Geometry cho điểm đi (Origin)
origin_points = gpd.points_from_xy(gt_df['ORIGIN_SUBZONE_X'], gt_df['ORIGIN_SUBZONE_Y'])
# Tạo cột Geometry cho điểm đến (Destination)
dest_points = gpd.points_from_xy(gt_df['DESTINATION_SUBZONE_X'], gt_df['DESTINATION_SUBZONE_Y'])

# Tạo GeoDataFrame (Hệ tọa độ gốc là WGS84 - EPSG:4326)
gdf_origin = gpd.GeoDataFrame(gt_df, geometry=origin_points, crs="EPSG:4326")
gdf_dest = gpd.GeoDataFrame(gt_df, geometry=dest_points, crs="EPSG:4326")

# Chuyển sang SVY21 (EPSG:3414)
gdf_origin_svy21 = gdf_origin.to_crs(epsg=3414)
gdf_dest_svy21 = gdf_dest.to_crs(epsg=3414)

# Tính khoảng cách Euclidean trên mặt phẳng SVY21
# Kết quả trả về đơn vị là MÉT
gt_df['distance_meters'] = gdf_origin_svy21.geometry.distance(gdf_dest_svy21.geometry)

# Nếu muốn đổi sang KM
gt_df['distance_km'] = gt_df['distance_meters'] / 1000


# Categorize distances into Facebook bins
conditions = [
    (gt_df['distance_km'] < 1),
    (gt_df['distance_km'] >= 1) & (gt_df['distance_km'] < 10),
    (gt_df['distance_km'] >= 10) & (gt_df['distance_km'] < 100),
    (gt_df['distance_km'] >= 100)
]
# Facebook bin names
choices = ['0', '(0, 10)', '[10, 100)', '100+']
gt_df['category'] = np.select(conditions, choices, default='100+')

# Merge ORIGIN_SUBZONE with district mapping
gt_df = gt_df.merge(district_zone_df, left_on='ORIGIN_SUBZONE', right_on='zone_id', how='left')

# gt_df.to_csv(os.path.join(base_dir, 'gt_with_distance.csv'), index=False)

# Aggregate total counts for each category per district
gt_agg = gt_df.groupby(['district_id', 'district_name', 'category'])['COUNT'].sum().reset_index()


# Normalize within each district
gt_agg['total_district_trips'] = gt_agg.groupby('district_id')['COUNT'].transform('sum')
gt_agg['p_gt'] = gt_agg['COUNT'] / gt_agg['total_district_trips']
gt_agg.to_csv(os.path.join(base_dir, 'gt_with_distance.csv'), index=False)


print("\n2. Loading Facebook Data...")
fb_df = pd.read_csv(fb_file)

# Filter Singapore
if 'SGP' in fb_df['country'].unique():
    fb_df = fb_df[fb_df['country'] == 'SGP']

# FB data has gadm_id which perfectly matches our district_id (e.g. 'SGP.1_1')
fb_agg = fb_df.groupby(['gadm_id', 'home_to_ping_distance_category'])['distance_category_ping_fraction'].mean().reset_index()

# Normalize within each gadm_id to sum to 1
fb_agg['total_fb_frac'] = fb_agg.groupby('gadm_id')['distance_category_ping_fraction'].transform('sum')
fb_agg['p_fb'] = fb_agg['distance_category_ping_fraction'] / fb_agg['total_fb_frac']

fb_agg = fb_agg.rename(columns={
    'gadm_id': 'district_id',
    'home_to_ping_distance_category': 'category'
})

fb_agg.to_csv(os.path.join(base_dir, 'fb_agg.csv'), index=False)

print("\n3. Comparing Distributions PER DISTRICT...")

# Find all matching districts (e.g. SGP.1_1)
districts = set(gt_agg['district_id'].unique()).intersection(set(fb_agg['district_id'].unique()))

if not districts:
    print("ERROR: No matching districts between Ground Truth and Facebook Data!")
    print("GT Districts sample:", gt_agg['district_id'].unique()[:5])
    print("FB Districts sample:", fb_agg['district_id'].unique()[:5])
    exit()

print(f"-> Found {len(districts)} matching districts.\n")

epsilon = 1e-9

for dist in sorted(districts):
    dist_name = gt_agg[gt_agg['district_id'] == dist]['district_name'].iloc[0]
    print(f"=== DISTRICT: {dist} ({dist_name}) ===")
    
    gt_dist = gt_agg[gt_agg['district_id'] == dist]
    fb_dist = fb_agg[fb_agg['district_id'] == dist]
    
    # Merge to align categories
    comparison = pd.DataFrame({'category': choices})
    comparison = comparison.merge(gt_dist[['category', 'p_gt']], on='category', how='left').fillna(0)
    comparison = comparison.merge(fb_dist[['category', 'p_fb']], on='category', how='left').fillna(0)

    # Avoid exact zeros for KL Divergence
    comparison['p_gt_calc'] = comparison['p_gt'] + epsilon
    comparison['p_fb_calc'] = comparison['p_fb'] + epsilon

    comparison['p_gt_calc'] = comparison['p_gt_calc'] / comparison['p_gt_calc'].sum()
    comparison['p_fb_calc'] = comparison['p_fb_calc'] / comparison['p_fb_calc'].sum()

    P = comparison['p_gt_calc'].values
    Q = comparison['p_fb_calc'].values

    # Divergence
    kl_pq = entropy(P, Q)
    M = 0.5 * (P + Q)
    js_div = 0.5 * entropy(P, M) + 0.5 * entropy(Q, M)
    
    print(f"KL Divergence: {kl_pq:.4f} | JS Divergence: {js_div:.4f}")
    
    for _, row in comparison.iterrows():
        cat = row['category']
        diff = row['p_gt'] - row['p_fb']
        if abs(diff) > 0.01:  # Only print noticeable differences (> 1%)
            if diff > 0:
                print(f"  - Bin '{cat:<10}': GT cao hơn FB {diff*100:5.2f}%")
            else:
                print(f"  - Bin '{cat:<10}': GT thấp hơn FB {-diff*100:5.2f}%")
        # print(row['p_gt'], row['p_fb'])
    print("-" * 50)
# save probilty ground truth to csv file with column district_id, category, p_gt
gt_agg.to_csv(os.path.join(base_dir, 'gt_prob.csv'), index=False)
print("\nDone Analysis.")


