import json
import pandas as pd
import glob
import os
import geopandas as gpd

def read_multiple_csv_files(directory_path='./', pattern='*.csv'):
    """
    Read multiple CSV files from a directory and combine them into one DataFrame
    """
    # Get list of CSV files
    search_pattern = os.path.join(directory_path, pattern)
    files = glob.glob(search_pattern)
    
    if not files:
        print("No CSV files found!")
        return None
    
    dfs = []
    successful_files = 0
    
    for file in files:
        try:
            print(f"Reading {file}...")
            df = pd.read_csv(file)
            df['source_file'] = os.path.basename(file)
            dfs.append(df)
            successful_files += 1
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"Successfully read {successful_files} files. Total rows: {len(combined_df)}")
       
        return combined_df
    else:
        print("No files were successfully read.")
        return None

# combined_data = read_multiple_csv_files('..', '*.csv')
def get_probability_per_10_cell(combined_data, gid):
    # Usage
    combined_data = combined_data[combined_data["gadm_id"] == gid]
    combined_data = combined_data[(combined_data['home_to_ping_distance_category'] == '(0, 10)')]
    if combined_data is not None and not combined_data.empty:
        # print("Filtered data shape:", combined_data.shape)
        # print("Sample values:")
        # print(combined_data["distance_category_ping_fraction"].head())
        # If you want the first value as float
        if len(combined_data) > 0:
            # print("First value:", float(combined_data["distance_category_ping_fraction"].iloc[0]))
            return float(combined_data["distance_category_ping_fraction"].iloc[0])
    else:
        print("No data found after filtering.")
        return 0
    
def get_probability_per_cell(combined_data, gid):
    # Usage
    combined_data = combined_data[combined_data["gadm_id"] == gid]
    combined_data = combined_data[(combined_data['home_to_ping_distance_category'] == '0')]
    if combined_data is not None and not combined_data.empty:
        # print("Filtered data shape:", combined_data.shape)
        # print("Sample values:")
        # print(combined_data["distance_category_ping_fraction"].head())
        # If you want the first value as float
        if len(combined_data) > 0:
            # print("First value:", float(combined_data["distance_category_ping_fraction"].iloc[0]))
            return float(combined_data["distance_category_ping_fraction"].iloc[0])
    else:
        print("No data found after filtering.")
        return 0
 
geojson_file = "detail_pois.geojson"
cell_gdf = gpd.read_file(geojson_file)

# Ensure 'prob_0' column exists
if 'prob_0' not in cell_gdf.columns:
    cell_gdf['prob_0'] = None

# Ensure 'prob_0' column exists
if 'prob_10' not in cell_gdf.columns:
    cell_gdf['prob_10'] = None

combined_data = read_multiple_csv_files('../map', '*2025-12-17.csv')

cell_gdf["prob_0"] = 0.0
cell_gdf["prob_10"] = 0.0

# print(combined_data)
for index, row in cell_gdf.iterrows():
    new_gid = row["district"]
    # print("a", new_gid)
    gid_dp = combined_data[combined_data["gadm_id"] == new_gid]
    
    gid = gid_dp["gadm_id"].values
    # print(gid)
    if gid.shape[0] > 0:
        # print(gid[0])
        prob = get_probability_per_cell(gid_dp, gid[0])
        # print(f"Setting prob for {gid}: {prob}")
        cell_gdf.at[index, "prob_0"] = prob

        prob_10 = get_probability_per_10_cell(gid_dp, gid[0])
        # print(f"Setting prob for {gid}: {prob_10}")
        cell_gdf.at[index, "prob_10"] = prob_10

cell_gdf.to_file(geojson_file, driver='GeoJSON')