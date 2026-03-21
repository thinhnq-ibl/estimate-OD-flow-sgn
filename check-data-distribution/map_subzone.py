import geopandas as gpd
import pandas as pd
import os

## data zone in map/sub_zone/data_sgp_subzone.shp
## data district in map/gadm41_SGP_shp/gadm41_SGP_1.shp
## find district of each zone
## if zone is in multiple districts, assign to the district with the largest area
## if zone is not in any district, assign to the nearest district
## save district_zone.csv with columns: zone_id, district_id, district_name

base_dir = os.path.dirname(os.path.abspath(__file__))
zone_path = os.path.join(base_dir, "../map/sub_zone/data_sgp_subzone.shp")
district_path = os.path.join(base_dir, "../map/gadm41_SGP_shp/gadm41_SGP_1.shp")

print("Loading Shapefiles...")
zone_gdf = gpd.read_file(zone_path)
district_gdf = gpd.read_file(district_path)

# Reproject to Singapore CRS (EPSG:3414) for accurate area calculations in square meters
print("Reprojecting to ESPG:3414 for precise area calculations...")
original_crs = zone_gdf.crs
zone_gdf = zone_gdf.to_crs(epsg=3414)
district_gdf = district_gdf.to_crs(epsg=3414)

# Keep track of original zone rows
zone_gdf['zone_tmp_id'] = zone_gdf.index

print("Calculating intersections...")
# Overlay to find all intersections between zones and districts
intersection = gpd.overlay(zone_gdf, district_gdf, how='intersection', keep_geom_type=False)
intersection['intersect_area'] = intersection.geometry.area

# Find the district with the maximum intersection area for each zone
max_intersect = intersection.sort_values('intersect_area', ascending=False).drop_duplicates(subset=['zone_tmp_id'])

# Distinguish matched vs unmatched
matched_zones_ids = max_intersect['zone_tmp_id'].tolist()
unmatched_zones = zone_gdf[~zone_gdf['zone_tmp_id'].isin(matched_zones_ids)].copy()

dist_columns = [c for c in district_gdf.columns if c != 'geometry']
final_gdf_parts = []

if not max_intersect.empty:
    # Use the ORIGINAL, uncut geometries for matched zones
    matched_original = zone_gdf.loc[max_intersect['zone_tmp_id']].copy()
    
    # Transfer the district properties of the largest overlap back to the original shapes
    for col in dist_columns:
        mapping = max_intersect.set_index('zone_tmp_id')[col]
        matched_original[col] = matched_original['zone_tmp_id'].map(mapping)
        
    final_gdf_parts.append(matched_original)
    
print(f"-> Matched {len(max_intersect)} zones by intersection.")

if not unmatched_zones.empty:
    print(f"-> Found {len(unmatched_zones)} zones with NO intersection. Applying nearest neighbor search...")
    # sjoin_nearest will securely find the closest district boundary for any outer zones
    nearest = gpd.sjoin_nearest(unmatched_zones, district_gdf, how='left', distance_col='nearest_dist')
    nearest = nearest.drop(columns=['index_right', 'nearest_dist'])
    final_gdf_parts.append(nearest)

print("Merging final result...")
final_gdf = pd.concat(final_gdf_parts, ignore_index=True)

# Clean up helper column
final_gdf = final_gdf.drop(columns=['zone_tmp_id'])

# Revert back to original CRS if preferred, else keep 3414. We'll keep original:
final_gdf = final_gdf.to_crs(original_crs)

out_path = os.path.join(base_dir, "../map/district_zone.shp")
print(f"Saving to {out_path}...")
final_gdf.to_file(out_path)

# Save district_zone.csv with columns: zone_id, district_id, district_name
print("Saving CSV mapping...")
csv_out_path = os.path.join(base_dir, "../map/district_zone.csv")
try:
    # Map based on standard column names for these shapefiles
    csv_df = final_gdf[['SUBZONE_C', 'GID_1', 'NAME_1']].copy()
    csv_df.columns = ['zone_id', 'district_id', 'district_name']
    csv_df.to_csv(csv_out_path, index=False)
    print(f"Saved CSV to {csv_out_path}")
except KeyError as e:
    print(f"Could not find exact columns for CSV: {e}. Please verify column names in shapefiles.")

print("Done!")
