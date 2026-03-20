import pandas as pd

# Load the dataset
# Replace 'your_data.csv' with the actual filename
df = pd.read_csv('../share_data/aggregated_trips.csv')

# Group by destination coordinates and sum the COUNT column
aggregated_df = df.groupby(['DESTINATION_SUBZONE', 'DESTINATION_SUBZONE_X', 'DESTINATION_SUBZONE_Y'], as_index=False)['COUNT'].sum()

# Sort the results by count in descending order
aggregated_df = aggregated_df.sort_values(by='DESTINATION_SUBZONE', ascending=False)

# Display the result
print(aggregated_df.head())

# Save the aggregated data to a new CSV file
aggregated_df.to_csv('aggregated_destination_counts.csv', index=False)