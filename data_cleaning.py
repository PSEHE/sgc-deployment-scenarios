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
sites_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'candidate_sites_campuses.csv')

sites_df_raw = pd.read_csv(sites_path)
sites_df = sites_df_raw.loc[sites_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]

occ_limits = pd.DataFrame({'cat_site':['W', 'CC', 'Pri', 'Sec', 'Coll'], 'sqft_pp':[15, 15, 15, 15, 15]})
#occ_limits = pd.DataFrame({'cat_site':['W', 'CC', 'Pri', 'Sec', 'Coll'], 'sqft_pp':[0.85, 0.85, 0.75, 0.75, 0.75]})

site_occ_df = pd.merge(sites_df, occ_limits, on = 'cat_site')
site_occ_df['occ_site'] = site_occ_df['SQFT_ROOF']/site_occ_df['sqft_pp']
site_occ_df = site_occ_df.loc[:, ['id_site', 'SQFT_ROOF', 'cat_site', 'occ_site']]

site_occ_dict = {}

for i in range(len(site_occ_df)):

    id_site = site_occ_df.iloc[i].loc['id_site']
    occ_site = site_occ_df.iloc[i].loc['occ_site']

    site_occ_dict[id_site] = occ_site

site_sqft_dict = {}

for i in range(len(site_occ_df)):

    id_site = site_occ_df.iloc[i].loc['id_site']
    occ_site = site_occ_df.iloc[i].loc['SQFT_ROOF']

    site_sqft_dict[id_site] = occ_site

##########################################
###### GET POPULATION DATA
# %%codecell
blockgroup_pop_df = pd.read_csv('data/bg_ca_19/blockgroup_pop_CA_19.csv')

blockgroup_pop_dict = {}

for i in range(len(blockgroup_pop_df)):

    blockgroup = blockgroup_pop_df.iloc[i].loc['GISJOIN']
    pop = blockgroup_pop_df.iloc[i].loc['POP']

    blockgroup_pop_dict[blockgroup] = pop

##########################################
###### MAKE DICTIONARY WITH blockgroup, site PAIR TUPLE AS KEY
# %%codecell
dist_to_site_df = pd.read_csv('data/distmatrix_contracosta.csv')
dist_to_site_df.set_index('Unnamed: 0', inplace = True)
dist_to_site_df.index.name = None

dist_to_site_dict = {}

for blockgroup in dist_to_site_df.index:
    for site in dist_to_site_df.columns:
        if dist_to_site_df.loc[blockgroup, site] == dist_to_site_df.loc[blockgroup, site]:
            dist_to_site_dict[tuple([blockgroup, site])] = dist_to_site_df.loc[blockgroup, site]

##########################################
###### READ HEAT DAY DATA
# %%codecell
heatdays_df = pd.read_csv('data/bg_ca_19/bg19_heatdays_avg00to13.csv')

heatdays_df = heatdays_df.loc[:, ['GISJOIN', 'MEAN']].sort_values('MEAN', ascending = False)

##########################################

region_df = pd.read_csv('data/candidate_site_campuses_2021-11-17/candidate_sites_campuses.csv')
region_df = region_df.loc[region_df['cat_site'] != 'X', ['id_site', 'REGION']]

site_region_df = region_df.merge(site_occ_df, on = 'id_site')

reg_pop = blockgroup_pop_df.groupby('REGION').sum()
reg_site = site_region_df.groupby('REGION').sum().loc[:,'occ_site']

regions = reg_pop.merge(reg_site, on = 'REGION')
regions['CAP_PP'] = regions['occ_site']/regions['POP']

##########################################
##### SCALE CES TO BG

# Derived by selecting cols from CES, NRI spatial join csv, which is too large to push to gitsite
bg_ces_df = pd.read_csv('data/bg_ca_19/bg19_ces_indicators.csv')

pct_cols = ['PCT_LESSHS', 'PCT_UNEMP', 'PCT_RENT', 'PCT_LINGISO', 'PCT_POV', 'RATE_ASTH', 'RATE_LBW', 'RATE_CVD']

for pct_col in pct_cols:

    pctl_col = 'PCTL_' + pct_col.split('_')[1]
    bg_ces_df[pctl_col] = 100*bg_ces_df[pct_col].rank(pct = True)

senspop_cols = ['PCTL_ASTH', 'PCTL_CVD', 'PCTL_LBW']
ses_cols = ['PCTL_LESSHS', 'PCTL_UNEMP', 'PCTL_RENT', 'PCTL_LINGISO', 'PCTL_POV']

bg_ces_df['SCORE_SENSPOP'] = bg_ces_df[senspop_cols].mean(axis = 1)
bg_ces_df['SCORE_SES'] = bg_ces_df[ses_cols].mean(axis = 1)
bg_ces_df['SCORE_POP'] = bg_ces_df[['SCORE_SES', 'SCORE_SENSPOP']].mean(axis = 1)/10

bg_ces_df['SCORE_CI_BG'] = bg_ces_df['SCORE_POP']*bg_ces_df['SCORE_POLLUT']
bg_ces_df['SCORE_PCTL_CI_BG'] = 100*bg_ces_df['SCORE_CI_BG'].rank(pct = True)

bg_ces_df = bg_ces_df.loc[:, ['GISJOIN', 'SCORE_PCTL_CI_BG']]




##
