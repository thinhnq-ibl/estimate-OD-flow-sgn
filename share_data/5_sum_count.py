import pandas as pd

# 1. Load the dataset
# Replace 'your_file.csv' with the actual path to your file
df = pd.read_csv('../share_data/bias_correct_data_seoul_pcm_2021.csv')

# 2. Group by Origin and Destination subzones
# We also include the X/Y coordinates in the grouping so they aren't lost, 
# as they are constant for each subzone.
aggregated_df = df.groupby(
    ['ORIGIN_SUBZONE', 'DESTINATION_SUBZONE', 
     'ORIGIN_SUBZONE_X', 'ORIGIN_SUBZONE_Y', 
     'DESTINATION_SUBZONE_X', 'DESTINATION_SUBZONE_Y']
)['COUNT'].sum().reset_index()

# 3. Sort by COUNT descending to see the busiest routes first
aggregated_df = aggregated_df.sort_values(by='COUNT', ascending=False)

# 4. Display or Save the results
print(aggregated_df.head())
aggregated_df.to_csv('aggregated_trips.csv', index=False)