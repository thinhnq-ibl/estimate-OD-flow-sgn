# Map subzone to district to get Facebook movement distribution.
- Each subzone has probability movement to the bins.
- Ground Truth Bin prob: calculate by data
- Facebook bin prob: Meta provide
# Get Population, get POIs for subzone
- Get popwold
- POIs: 
    + 'amenity': True, 'shop': True, 'tourism': True,
    'leisure': True, 'office': True, 'public_transport': True
# Normalize ground truth 
- get total trips
- get percent of trips for each subzone
- normalize by total trips
# Gen OD flow
- Calculate distance from one subzone to all other subzone.
- Categorize to : 'under_1km', '1km-10km', '10km-100km'
- Weight to POIs
POI_WEIGHTS = {
    'office': 15,
    'public_transport': 50,
    'shop': 10,
    'amenity': 2,
    'tourism': 4,
    'leisure': 1
}
- origin_mass: pop_count + 1
- destination_mass: POI_WEIGHT * POI_COUNT + 1
- Calculate s_ij by distance from i to j.
- Calculate A_ij = (x_i * x_j)/((x_i + s_ij)*(x_i + x_j + s_ij))
    - x_i: population (source)
    - x_j: destination_mass (destination)
    - s_ij: sum all x_k  k_distance < j_distance (sum all destination_mass)

- Bin1
    - sum_Aij = all A_ij in bin1
    - prob = (rw['raw_Aij'] / sum_Aij * p0)
- Bin2
    - sum_Aij = all A_ij in bin2
    - prob = (rw['raw_Aij'] / sum_Aij * p10)
- Bin3
    - sum_Aij = all A_ij in bin3
    - prob = (rw['raw_Aij'] / sum_Aij * (1-p0-p10))

- Calculate trips beween subzone pair
    - prob * T_ij

# Normalize gen OD flow
- get total trips
- get percent of trips for each subzone
- normalize by total trips

# Calculate CPC
- Calculate CPC for Gen data and ground truth