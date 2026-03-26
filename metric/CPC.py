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


def evaluate_model_refined(df_obs, df_pred, model_name):
    # 1. Pre-process and Aggregate
    for df in [df_obs, df_pred]:
        df['norm_total_in'] = pd.to_numeric(df['norm_total_in'], errors='coerce').fillna(0)
    
    # Aggregate to ensure unique pairs
    obs_agg = df_obs.groupby(['subzone_id', 'neighbor_subzone_id'])['norm_total_in'].sum().reset_index()
    pred_agg = df_pred.groupby(['subzone_id', 'neighbor_subzone_id'])['norm_total_in'].sum().reset_index()

    # 2. Align via Outer Merge
    merged = pd.merge(
        obs_agg, pred_agg, 
        on=['subzone_id', 'neighbor_subzone_id'], 
        how='outer', 
        suffixes=('_obs', '_pred')
    ).fillna(0)

    y_true = merged['norm_total_in_obs'].values
    y_pred = merged['norm_total_in_pred'].values

    # 3. Core Metrics
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # CPC Calculation
    intersection = np.minimum(y_true, y_pred).sum()
    total_sum = y_true.sum() + y_pred.sum()
    cpc = (2.0 * intersection) / total_sum if total_sum > 0 else 0.0

    # 4. Error Analysis
    merged['abs_error'] = np.abs(y_true - y_pred)
    
    # Print summary
    print(f"--- Results for {model_name} ---")
    print(f"R2 Score:  {r2:.4f}")
    print(f"RMSE:      {rmse:.4f}")
    print(f"CPC:       {cpc:.4f}")
    
    return merged, {"R2": r2, "RMSE": rmse, "CPC": cpc}

# cpc_score = fast_cpc(gpd_real, gpd_simulate)
scores = evaluate_model_refined(gpd_real, gpd_simulate, "GEOGloWS")
print(f"CPC Score: {scores}")
