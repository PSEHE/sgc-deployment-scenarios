##########################################
###### LIBRARY PACKAGES
# %%codecell

import pandas as pd
import os
import matplotlib.pyplot as plt

##########################################
###### GENERATE SITE CAPACITY DATA
# %%codecell
#https://ccpia.org/occupancy-load-signs/
from distance_matrix_calculation import hubs_gdf

occ_limits = pd.DataFrame({'cat_site':['W', 'CC', 'Pri', 'Sec', 'Coll'], 'sqft_pp':[15, 15, 15, 15, 15]})
#occ_limits = pd.DataFrame({'cat_site':['W', 'CC', 'Pri', 'Sec', 'Coll'], 'sqft_pp':[0.85, 0.85, 0.75, 0.75, 0.75]})

hub_occ_df = pd.merge(hubs_gdf, occ_limits, on = 'cat_site')
hub_occ_df['occ_site'] = hub_occ_df['SQFT_ROOF']/hub_occ_df['sqft_pp']
hub_occ_df = hub_occ_df.loc[:, ['id_site', 'SQFT_ROOF', 'cat_site', 'occ_site']]

hub_occ_dict = {}

for i in range(len(hub_occ_df)):

    id_site = hub_occ_df.iloc[i].loc['id_site']
    occ_site = hub_occ_df.iloc[i].loc['occ_site']

    hub_occ_dict[id_site] = occ_site

hub_sqft_dict = {}

for i in range(len(hub_occ_df)):

    id_site = hub_occ_df.iloc[i].loc['id_site']
    occ_site = hub_occ_df.iloc[i].loc['SQFT_ROOF']

    hub_sqft_dict[id_site] = occ_site

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

##########################################
###### READ HEAT DAY DATA
# %%codecell
heatdays_df = pd.read_csv('data/bg_ca_19/bg19_heatdays_avg00to13.csv')

heatdays_df = heatdays_df.loc[:, ['GISJOIN', 'MEAN']].sort_values('MEAN', ascending = False)

##########################################

region_df = pd.read_csv('data/candidate_site_campuses_2021-11-17/candidate_sites_campuses.csv')
region_df = region_df.loc[region_df['cat_site'] != 'X', ['id_site', 'REGION']]

site_region_df = region_df.merge(hub_occ_df, on = 'id_site')

reg_pop = cengeo_pop_df.groupby('REGION').sum()
reg_site = site_region_df.groupby('REGION').sum().loc[:,'occ_site']

regions = reg_pop.merge(reg_site, on = 'REGION')
regions['CAP_PP'] = regions['occ_site']/regions['POP']


























##
