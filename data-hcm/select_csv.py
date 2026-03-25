
import geopandas as gpd
import pandas as pd
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))
row = pd.read_csv(os.path.join(base_dir, './ket_qua_quan_trac_1.csv'))

result = []
for index, row in row.iterrows():
    result.append({
        'tt': row.iat[0],
        'vung': row.iat[1],
        'ma_vds': row.iat[2],
        'duong': row.iat[3],
        'doan': row.iat[4],
        'lan': row.iat[5],
        'loai1': row.iat[14],
        'loai2': row.iat[15],
        'loai3': row.iat[16],
        'loai4': row.iat[17],
        'loai5': row.iat[18],   
        'van_toc': row.iat[19],
        'PCU': row.iat[20],
        'LOS': row.iat[21],
    })

df = pd.DataFrame(result)
df.to_csv(os.path.join(base_dir, './ket_qua_quan_trac_1_selected.csv'), index=False)

    