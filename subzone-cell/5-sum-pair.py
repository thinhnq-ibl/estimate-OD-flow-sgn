import pandas as pd

# Load the files
all_flow_cell_df = pd.read_csv("../map/data_sgp_pcm_trip.csv")

# sum pair
# the same origin and destination, sum the flow
all_flow_cell_df = all_flow_cell_df.groupby(["ORIGIN_SUBZONE", "DESTINATION_SUBZONE"])["COUNT"].sum().reset_index()

# Save the final geodataframe
all_flow_cell_df.to_csv("../map/data_trip_sum.csv", index=False)
print("Successfully processed and saved to ../map/data_trip_sum.csv")