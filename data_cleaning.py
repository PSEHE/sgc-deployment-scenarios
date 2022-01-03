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

hub_occ_dict = {}

for i in range(len(hub_occ_df)):

    id_site = hub_occ_df.iloc[i].loc['id_site']
    occ_site = hub_occ_df.iloc[i].loc['occ_site']

    hub_occ_dict[id_site] = occ_site

##########################################
###### GET POPULATION DATA
# %%codecell
cengeo_pop_df = pd.read_csv('data/bg_ca_19/blockgroup_pop_CA_19.csv')

cengeo_pop_dict = {}

for i in range(len(cengeo_pop_df)):

    cengeo = cengeo_pop_df.iloc[i].loc['GISJOIN']
    pop = cengeo_pop_df.iloc[i].loc['POP']

    cengeo_pop_dict[cengeo] = pop

##########################################
###### MAKE DICTIONARY WITH CENGEO, HUB PAIR TUPLE AS KEY
# %%codecell
from distance_matrix_calculation import dist_to_hub_df

dist_to_hub_dict = {}

for cengeo in dist_to_hub_df.index:
    for hub in dist_to_hub_df.columns:
        if dist_to_hub_df.loc[cengeo, hub] == dist_to_hub_df.loc[cengeo, hub]:
            dist_to_hub_dict[tuple([cengeo, hub])] = dist_to_hub_df.loc[cengeo, hub]
