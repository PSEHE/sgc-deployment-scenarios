##########################################
###### LIBRARY PACKAGES
# %%codecell

import pandas as pd
import os

##########################################
###### GENERATE SITE CAPACITY DATA
# %%codecell
#https://ccpia.org/occupancy-load-signs/
from distance_matrix_calculation import hubs_gdf

occ_limits = pd.DataFrame({'cat_site':['W', 'CC', 'Pri', 'Sec', 'Coll'], 'sqft_pp':[15, 15, 50, 50, 50]})

hub_occ_df = pd.merge(hubs_gdf, occ_limits, on = 'cat_site')
hub_occ_df['occ_site'] = hub_occ_df['SQFT_ROOF']/hub_occ_df['sqft_pp']
hub_occ_df = hub_occ_df.loc[:, ['id_site', 'cat_site', 'occ_site']]

##########################################
###### GET POPULATION DATA
# %%codecell

from distance_matrix_calculation import dist_to_hub_df

dist_to_hub_dict = {}

for cengeo in dist_to_hub_df.index:
    for hub in dist_to_hub_df.columns:
        if dist_to_hub_df.loc[cengeo, hub] == dist_to_hub_df.loc[cengeo, hub]:
            dist_to_hub_dict[tuple([cengeo, hub])] = dist_to_hub_df.loc[cengeo, hub]
