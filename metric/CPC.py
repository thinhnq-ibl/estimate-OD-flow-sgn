import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error

# 1. Prepare your data (Example: Observed vs GEOGloWS Simulated)
# observed = [values...]
# simulated = [values...]

# Dummy data for demonstration
# np.random.seed(42)
# observed = np.random.uniform(10, 100, 50)
# simulated = observed + np.random.normal(0, 10, 50) # Simulated with some error



# Determine path relative to this script so the module can be run from anywhere
import os
base_dir = os.path.abspath(os.path.dirname(__file__))

# Read as CSV (not GeoDataFrame) and ensure numeric columns
gpd_real_path = os.path.join(base_dir, "..", "gen-cell-flow-for-test", "normalized_real_flow.csv")
gpd_simulate_path = os.path.join(base_dir, "..", "gen-OD-flow", "normalized_gen_flow.csv")

# use pandas to read
print(f"Loading real data from {gpd_real_path}")
print(f"Loading simulated data from {gpd_simulate_path}")

gpd_real = pd.read_csv(gpd_real_path)
gpd_simulate = pd.read_csv(gpd_simulate_path)



# Ensure in_amount is numeric (in case of string/object type)
gpd_real['norm_total_in'] = pd.to_numeric(gpd_real['norm_total_in'], errors='coerce').fillna(0)
gpd_simulate['norm_total_in'] = pd.to_numeric(gpd_simulate['norm_total_in'], errors='coerce').fillna(0)

# def fast_cpc(df_obs, df_pred):
#     """
#     High-performance CPC calculation for large datasets.
#     """
#     # Ensure in_amount columns are numeric
#     df_obs = df_obs.copy()
#     df_pred = df_pred.copy()
#     df_obs['norm_total_in'] = pd.to_numeric(df_obs['norm_total_in'], errors='coerce')
#     df_pred['norm_total_in'] = pd.to_numeric(df_pred['norm_total_in'], errors='coerce')

#     # 1. Use an inner merge to find the intersection of flows
#     merged = pd.merge(
#         df_obs[['cell_id', 'neighbor_id', 'norm_total_in']], 
#         df_pred[['cell_id', 'neighbor_id', 'norm_total_in']], 
#         on=['cell_id', 'neighbor_id'], 
#         suffixes=('_obs', '_pred')
#     )
#     # 2. Convert columns to NumPy arrays (zero-copy view if possible)
#     obs_flows = merged['norm_total_in_obs'].values.astype(float)
#     pred_flows = merged['norm_total_in_pred'].values.astype(float)

#     # 3. Vectorized minimum and sums
#     intersection_sum = np.minimum(obs_flows, pred_flows).sum()

#     # Calculate totals from the original dataframes to account for flows that might exist in one but not the other
#     total_obs = df_obs['norm_total_in'].sum()
#     total_pred = df_pred['norm_total_in'].sum()

#     # 4. Final CPC ratio
#     cpc = (2.0 * intersection_sum) / (total_obs + total_pred) if (total_obs + total_pred) != 0 else 0.0
#     return cpc

def evaluate_model(df_obs, df_pred, model_name):
    """
    Aligns data via an outer merge (to penalize flows predicted where none exist, 
    and vice versa) and calculates R2, RMSE, and CPC.
    """
    # Ensure numeric types
    df_obs['norm_total_in'] = pd.to_numeric(df_obs['norm_total_in'], errors='coerce').fillna(0)
    df_pred['norm_total_in'] = pd.to_numeric(df_pred['norm_total_in'], errors='coerce').fillna(0)

    # Aggregate duplicates by grouping cell_id and neighbor_id strictly to prevent cartesian explosion
    df_obs = df_obs.groupby(['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id'], as_index=False)['norm_total_in'].sum()
    df_pred = df_pred.groupby(['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id'], as_index=False)['norm_total_in'].sum()

    # Outer merge to align the 95,000 cell pairs correctly
    merged = pd.merge(
        df_obs[['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id', 'norm_total_in']], 
        df_pred[['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id', 'norm_total_in']], 
        on=['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id'], 
        how='outer',
        suffixes=('_obs', '_pred')
    ).fillna(0) # Fill missing flows with 0

    # merged['distance'] = np.sqrt((merged['x_obs'] - merged['x_pred'])**2 + (merged['y_obs'] - merged['y_pred'])**2)
    high_error_phantom = merged[(merged['norm_total_in_obs'] == 0) & (merged['norm_total_in_pred'] > 1000)]
    print(high_error_phantom)
    
    y_true = merged['norm_total_in_obs'].values
    y_pred = merged['norm_total_in_pred'].values
    
    # Totals for CPC (use original dfs to preserve sum of all flows)
    total_obs = df_obs['norm_total_in'].sum()
    total_pred = df_pred['norm_total_in'].sum()

    # Calculate Metrics
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    # compute CPC directly from the aligned arrays to avoid mismatched signatures
    intersection = np.minimum(y_true, y_pred).sum()
    cpc = (2.0 * intersection) / (total_obs + total_pred) if (total_obs + total_pred) != 0 else 0.0
    
    merged['error'] = abs(merged['norm_total_in_obs'] - merged['norm_total_in_pred'])
    print("Top 10 cặp dự đoán lệch nặng nhất:")
    print(merged.sort_values('error', ascending=False).head(10))
    
    try:
        pair_df = pd.read_csv(os.path.join(base_dir, "..", "gen-OD-flow", "categorized_cell_pairs.csv"), usecols=['cell_id', 'neighbor_id', 'category', 'distance_m', 'subzone_id', 'neighbor_subzone_id'])
        merged_dist = merged.merge(pair_df[['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id', 'category']], on=['cell_id', 'subzone_id', 'neighbor_id', 'neighbor_subzone_id'], how='left')
        print("\n\n--- PHÂN TÍCH SAI LỆCH THEO VÀNH ĐAI KHOẢNG CÁCH (CATEGORY) ---")
        stats = []
        for cat, group in merged_dist.groupby('category'):
            mae = group['error'].mean()
            sum_err = group['error'].sum()
            obs_sum = group['norm_total_in_obs'].sum()
            pred_sum = group['norm_total_in_pred'].sum()
            cpc_cat = 2 * group[['norm_total_in_obs', 'norm_total_in_pred']].min(axis=1).sum() / (obs_sum + pred_sum) if (obs_sum + pred_sum) > 0 else 0
            stats.append({'Category': cat, 'Count': len(group), 'MAE (Error TB)': mae, 'Tổng Error': sum_err, 'Tổng Obs': obs_sum, 'Tổng Pred': pred_sum, 'Nội bộ CPC': cpc_cat})
        
        stats_df = pd.DataFrame(stats).sort_values('Category')
        print(stats_df.to_string(index=False))
        print("\n")
    except Exception as e:
        print("Không thể phân tích theo khoảng cách:", e)

    return {"Model": model_name, "R2": r2, "RMSE": rmse, "CPC": cpc}, y_true, y_pred
# Example Usage:

# cpc_score = fast_cpc(gpd_real, gpd_simulate)
scores = evaluate_model(gpd_real, gpd_simulate, "GEOGloWS")
print(f"CPC Score: {scores}")
