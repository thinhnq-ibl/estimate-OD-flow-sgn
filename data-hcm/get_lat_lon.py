
import geopandas as gpd
import pandas as pd
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))
data = pd.read_csv(os.path.join(base_dir, './ket_qua_quan_trac_1_selected.csv'))

base_dir = os.path.dirname(os.path.abspath(__file__))
data2 = pd.read_csv(os.path.join(base_dir, './obser_data_2_4_25.csv'))

data["lat_st"] = np.nan
data["lon_st"] = np.nan
data["lat_en"] = np.nan
data["lon_en"] = np.nan

for index, row in data2.iterrows():
    if row.iat[2] > 0:
        data.loc[(data['loai1'] == row.iat[2]) & (data['loai2'] == row.iat[3]), 'lat_st'] = row.iat[10]
        data.loc[(data['loai1'] == row.iat[2]) & (data['loai2'] == row.iat[3]), 'lon_st'] = row.iat[11]
        data.loc[(data['loai1'] == row.iat[2]) & (data['loai2'] == row.iat[3]), 'lat_en'] = row.iat[12]
        data.loc[(data['loai1'] == row.iat[2]) & (data['loai2'] == row.iat[3]), 'lon_en'] = row.iat[13]

data.to_csv(os.path.join(base_dir, './ket_qua_quan_trac_1_selected_lat_lon.csv'), index=False)