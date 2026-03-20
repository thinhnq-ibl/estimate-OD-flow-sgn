import pandas as pd

# 1. Load the dataset
# Replace 'your_file.csv' with the actual path to your file
df = pd.read_csv('../map/data_sgp_pcm_trip.csv')
subzones_no_overlap = pd.read_csv('../share_data/subzones_no_overlap.csv')

# filter trips not contain subzones_no_overlap
df = df[~df['ORIGIN_SUBZONE'].isin(subzones_no_overlap['SUBZONE_C'])]
df = df[~df['DESTINATION_SUBZONE'].isin(subzones_no_overlap['SUBZONE_C'])]

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