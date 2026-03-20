import pandas as pd

# 1. Load your GeoJSON data
# Replace 'in_flow_cells_v2_distance.json' with your actual file path
gdf = pd.read_csv('all_flow_cell33.csv')
gdf = gdf[gdf['in_amount'] > 0]

# 2. Calculate the total sum from cell_id
total_in_flow = gdf.groupby('cell_id')['in_amount'].sum().reset_index()

# 5. Save the updated data to a new file
total_in_flow.to_csv('only_cell_out.csv', index=False)

# Display the first few rows to verify
