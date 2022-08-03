#!/usr/bin/env python
# coding: utf-8

# In[1]:

import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import haversine as hs

# ### Get site max occupancy

# In[11]:


#https://ccpia.org/occupancy-load-signs/
sites_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'candidate_sites_campuses.csv')

sites_df_raw = pd.read_csv(sites_path)
sites_df = sites_df_raw.loc[sites_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]

site_sqft_df = sites_df.loc[:, ['id_site', 'SQFT_ROOF']]

site_sqft_dict = {}

for i in range(len(site_sqft_df)):

    id_site = site_sqft_df.iloc[i].loc['id_site']
    sqft_site = site_sqft_df.iloc[i].loc['SQFT_ROOF']

    site_sqft_dict[id_site] = sqft_site


# In[ ]:


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


# ### Create dictionary of blockgroup populations

# In[3]:


cengeo_pop_df = pd.read_csv('data/bg_ca_19/blockgroup_pop_CA_19.csv')

cengeo_pop_dict = {}

for i in range(len(cengeo_pop_df)):

    cengeo = cengeo_pop_df.iloc[i].loc['GISJOIN']
    pop = cengeo_pop_df.iloc[i].loc['POP']

    cengeo_pop_dict[cengeo] = pop
blockgroup_pop_dict = cengeo_pop_dict

# ### Create dictionary of hub/blockgroup pairwise distances

# In[4]:


dist_to_site_contra_costa_df = pd.read_csv('data/distance_matrices/distmatrix_contracosta.csv',index_col = 0)

dist_to_site_contra_costa_dict = {}

for cengeo in dist_to_site_contra_costa_df.index:
    for hub in dist_to_site_contra_costa_df.columns:
        if dist_to_site_contra_costa_df.loc[cengeo, hub] == dist_to_site_contra_costa_df.loc[cengeo, hub]:
            dist_to_site_contra_costa_dict[tuple([cengeo, hub])] = dist_to_site_contra_costa_df.loc[cengeo, hub]

dist_to_site_contra_costa_walk_df = pd.read_csv('data/distance_matrices/distmatrix_walk_contracosta.csv',index_col = 0)

dist_to_site_contra_costa_walk_dict = {}

for cengeo in dist_to_site_contra_costa_walk_df.index:
    for hub in dist_to_site_contra_costa_walk_df.columns:
        if dist_to_site_contra_costa_walk_df.loc[cengeo, hub] == dist_to_site_contra_costa_walk_df.loc[cengeo, hub]:
            dist_to_site_contra_costa_walk_dict[tuple([cengeo, hub])] = dist_to_site_contra_costa_walk_df.loc[cengeo, hub]

dist_to_site_contra_costa_walk_cf_df = pd.read_csv('data/distance_matrices/distmatrix_walk_cfcontracosta.csv',index_col = 0)

dist_to_site_contra_costa_walk_cf_dict = {}

for cengeo in dist_to_site_contra_costa_walk_cf_df.index:
    for hub in dist_to_site_contra_costa_walk_cf_df.columns:
        if dist_to_site_contra_costa_walk_cf_df.loc[cengeo, hub] == dist_to_site_contra_costa_walk_cf_df.loc[cengeo, hub]:
            dist_to_site_contra_costa_walk_cf_dict[tuple([cengeo, hub])] = dist_to_site_contra_costa_walk_cf_df.loc[cengeo, hub]

dist_to_site_richmond_df = pd.read_csv('data/distance_matrices/distmatrix_richmond.csv',index_col = 0)

dist_to_site_richmond_dict = {}

for cengeo in dist_to_site_richmond_df.index:
    for hub in dist_to_site_richmond_df.columns:
        if dist_to_site_richmond_df.loc[cengeo, hub] == dist_to_site_richmond_df.loc[cengeo, hub]:
            dist_to_site_richmond_dict[tuple([cengeo, hub])] = dist_to_site_richmond_df.loc[cengeo, hub]

dist_to_site_richmond_walk_df = pd.read_csv('data/distance_matrices/distmatrix_walk_richmond.csv',index_col = 0)

dist_to_site_richmond_walk_dict = {}

for cengeo in dist_to_site_richmond_walk_df.index:
    for hub in dist_to_site_richmond_walk_df.columns:
        if dist_to_site_richmond_walk_df.loc[cengeo, hub] == dist_to_site_richmond_walk_df.loc[cengeo, hub]:
            dist_to_site_richmond_walk_dict[tuple([cengeo, hub])] = dist_to_site_richmond_walk_df.loc[cengeo, hub]

dist_to_site_wilmington_df = pd.read_csv('data/distance_matrices/distmatrix_wilmington.csv',index_col = 0)

dist_to_site_wilmington_dict = {}

for cengeo in dist_to_site_wilmington_df.index:
    for hub in dist_to_site_wilmington_df.columns:
        if dist_to_site_wilmington_df.loc[cengeo, hub] == dist_to_site_wilmington_df.loc[cengeo, hub]:
            dist_to_site_wilmington_dict[tuple([cengeo, hub])] = dist_to_site_wilmington_df.loc[cengeo, hub]

dist_to_site_wilmington_walk_df = pd.read_csv('data/distance_matrices/distmatrix_walk_wilmington.csv',index_col = 0)

dist_to_site_wilmington_walk_dict = {}

for cengeo in dist_to_site_wilmington_walk_df.index:
    for hub in dist_to_site_wilmington_walk_df.columns:
        if dist_to_site_wilmington_walk_df.loc[cengeo, hub] == dist_to_site_wilmington_walk_df.loc[cengeo, hub]:
            dist_to_site_wilmington_walk_dict[tuple([cengeo, hub])] = dist_to_site_wilmington_walk_df.loc[cengeo, hub]

# ### Get blockgroup region

# In[6]:


region_df = pd.read_csv('data/candidate_site_campuses_2021-11-17/candidate_sites_campuses.csv')
region_df = region_df.loc[region_df['cat_site'] != 'X', ['id_site', 'REGION']]

site_region_df = region_df.merge(site_occ_df, on = 'id_site')

reg_pop = cengeo_pop_df.groupby('REGION').sum()
reg_site = site_region_df.groupby('REGION').sum().loc[:,'occ_site']

regions = reg_pop.merge(reg_site, on = 'REGION')
regions['CAP_PP'] = regions['occ_site']/regions['POP']


# ### Get blockgroup CES score

# In[7]:


# Derived by selecting cols from CES, NRI spatial join csv, which is too large to push to github
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

bg_ces_dict = {bg_ces_df.iloc[row]['GISJOIN']: round(0.01*bg_ces_df.iloc[row]['SCORE_PCTL_CI_BG'], 2) for row in bg_ces_df.index}


# ### Get cost per hub

# In[13]:


site_cost_dict = dict()
site_kw_occ_dict = dict()

people_per_kwh = 10

for site in site_sqft_dict:
    pv_kw = 0.007*site_sqft_dict[site]

    ba_kw = 0.42*pv_kw #This said pv_size originally but I think this is what was meant?
    ba_kwh = 0.046*site_sqft_dict[site]

    pv_cost_dollars = 4000*pv_kw*(pv_kw**-0.01)
    ba_cost_dollars = 840*ba_kw + 1000*ba_kwh*(ba_kwh**-0.019)

    site_cost_tot = pv_cost_dollars + ba_cost_dollars

    site_cost_dict[site] = site_cost_tot
    site_kw_occ_dict[site] = ba_kwh*people_per_kwh


# ### National Risk Index: Get Share of Resources to Allocate to Each County
# Expected annual loss equations on page 45 of NRI technical documentation
# https://www.fema.gov/sites/default/files/documents/fema_national-risk-index_technical-documentation.pdf
#
# Min-Max Normalized Values: (EAL^0.3 - 0.99*EAL^0.3) / (EAL_max^0.33 - EAL_min^0.33)

# In[ ]:


# Created for calculation of EALT score - no longer used due to switch to EALP, which can just be summed

def calculate_ealt_score(ealt_col):
    ealt_numerator = (ealt_col ** (1/3)) - (0.99*ealt_col.min() ** (1/3))
    ealt_denominator = (ealt_col.max() ** (1/3)) - (ealt_col.min() ** (1/3))

    return(ealt_numerator/ealt_denominator)


# ###### _Code to go from raw file with all indicators to file with just EAL indicators - the former is too large for github_
# bg_nri_indicators_all = pd.read_csv('../bg_ca_ces_nri_indicators_spatialjoin.csv')
#
# nri_cols = list(bg_nri_indicators_all.columns)
# annual_loss_cols = [col for col in nri_cols if str(col)[-4:-1] == 'EAL']
# annual_loss_cols.append('GISJOIN')
#
# bg_nri_eal_raw = bg_nri_indicators_all.loc[:,annual_loss_cols]
# bg_nri_eal_raw.fillna(0, inplace = True)
#
# bg_nri_eal_raw.to_csv('data/bg_ca_19/bg19_NRI_annualloss_score.csv', index = False)

# In[ ]:


bg_nri_eal_all = pd.read_csv('data/bg_ca_19/bg19_NRI_annualloss_score.csv')

ealp_cols_all = [col for col in bg_nri_eal_all if str(col)[-4:] == 'EALP']
ealp_cols = ['CWAV_EALP', 'ERQK_EALP', 'HWAV_EALP', 'ISTM_EALP', 'LNDS_EALP', 'RFLD_EALP', 'SWND_EALP', 'TSUN_EALP', 'VLCN_EALP', 'WFIR_EALP', 'WNTW_EALP']

bg_nri_ealp = bg_nri_eal_all.loc[:,ealp_cols]
bg_nri_ealp['TOT_EALP'] = bg_nri_ealp.sum(axis = 1)

bg_nri_ealp.insert(0, 'GISJOIN', bg_nri_eal_all['GISJOIN'])

ca_nri_ealp_tot = sum(bg_nri_ealp['TOT_EALP'])

bg_nri_ealp['PROP_EALP'] = bg_nri_ealp['TOT_EALP']/ca_nri_ealp_tot
bg_nri_ealp.insert(1, 'COUNTY_FIPS', bg_nri_ealp['GISJOIN'].str[3:7])


# In[ ]:


county_prop_ealp_df = bg_nri_ealp.groupby('COUNTY_FIPS').sum()['PROP_EALP']

county_prop_ealp_dict = {fips_code:county_prop_ealp_df.loc[fips_code] for fips_code in county_prop_ealp_df.index}

# ### National Risk Index: Prioritize by Population Vulnerability and Resilience

# ### Driving Population by Block Group
# Retrieve census data on proportion of households with a car, multiply block group
# population by this proportion to get proportion of people with car access by block group
driving_pop_path = os.path.join(os.getcwd(), 'data', 'nhgis0037_csv', 'nhgis0037_ds244_20195_blck_grp.csv')
bg_pop_path = os.path.join(os.getcwd(), 'data', 'bg_ca_19', 'blockgroup_pop_CA_19.csv')

driving_pop_df_raw = pd.read_csv(driving_pop_path)

# get proportion of occupied housing units with no vehicle
prop_no_car = pd.DataFrame({'GISJOIN': driving_pop_df_raw['GISJOIN'],
             'prop_no_car': (driving_pop_df_raw['AL0NE003'] + driving_pop_df_raw['AL0NE010'])/driving_pop_df_raw['AL0NE001']})

bg_pop_df_raw = pd.DataFrame(pd.read_csv(bg_pop_path))

no_car_df = bg_pop_df_raw.merge(prop_no_car, on = 'GISJOIN')
no_car_df['POP_no_car'] = no_car_df['POP']*no_car_df['prop_no_car']
no_car_df = no_car_df[['GISJOIN', 'POP_no_car']]

no_car_pop_dict = {}

for i in range(len(no_car_df)):

    cengeo = no_car_df.iloc[i].loc['GISJOIN']
    pop = no_car_df.iloc[i].loc['POP_no_car']

    no_car_pop_dict[cengeo] = pop

blockgroup_no_car_pop_dict = no_car_pop_dict

# ### Walkability scores by block group
walkability_path = os.path.join(os.getcwd(), 'data', 'EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv')
walkability_df_raw = pd.read_csv(walkability_path, dtype = {'GEOID10': str})

walkability_df = pd.DataFrame(walkability_df_raw.loc[walkability_df_raw['STATEFP'] == 6])

# Form correct GEOID
GISJOIN = 'G' + walkability_df['STATEFP'].astype(str).str.rjust(2, '0') + '0' +\
walkability_df['COUNTYFP'].astype(str).str.rjust(3, '0') + '0' +\
walkability_df['TRACTCE'].astype(str).str.rjust(6, '0') +\
walkability_df['BLKGRPCE'].astype(str).str.rjust(1, '0')

walkability_df['GISJOIN'] = GISJOIN

walkability_df = walkability_df[['GISJOIN', 'NatWalkInd']]

walkability_dict = {}

for i in range(len(walkability_df)):

    cengeo = walkability_df.iloc[i].loc['GISJOIN']
    walkability = walkability_df.iloc[i].loc['NatWalkInd']

    walkability_dict[cengeo] = walkability

blockgroup_walkability_dict = walkability_dict

# ### Wilmington walking distances (weighted average of survey responses)
survey = pd.read_csv(r'data/survey_cleaned.csv')
survey = pd.concat([survey, survey['geometry'].str.split(', ', expand=True).rename(columns={0:'Latitude', 1:'Longitude'})], axis = 1)
nad83 = 'EPSG:4269'
survey.Latitude = pd.to_numeric(survey.Latitude)
survey.Longitude = pd.to_numeric(survey.Longitude)
gdf = gpd.GeoDataFrame(survey, geometry=gpd.points_from_xy(survey.Longitude, survey.Latitude), crs = nad83)

bgs_path = os.path.join(os.getcwd(), 'data', 'bg_ca_19', 'shp', 'blockgroup_CA_19.shp')
bgs_gdf = gpd.read_file(bgs_path)
bgs_gdf = bgs_gdf.to_crs(nad83)
bgs_lons = [float(intpt) for intpt in bgs_gdf['INTPTLON']]
bgs_lats = [float(intpt) for intpt in bgs_gdf['INTPTLAT']]
bgs = pd.DataFrame(bgs_gdf[['GISJOIN', 'COUNTYFP']])
bgs['LON'] = bgs_lons
bgs['LAT'] = bgs_lats
bgs_pt_geom = gpd.points_from_xy(x = bgs.LON,y = bgs.LAT, crs = nad83)
bgs_pt_gdf = gpd.GeoDataFrame(bgs, geometry = bgs_pt_geom, crs = nad83)

# Building Wilmington shapefile
wilmington_path = os.path.join(os.getcwd(), 'data', 'LA_Times_Neighborhood_Boundaries', 'LA_Times_Neighborhood_Boundaries.shp')
wilmington_gdf = gpd.read_file(wilmington_path)
wilmington_gdf['geometry'] = wilmington_gdf['geometry'].unary_union
del wilmington_gdf['OBJECTID']
wilmington_shp = wilmington_gdf.unary_union

bgs_area_gdf = bgs_pt_gdf.loc[bgs_pt_gdf.within(wilmington_shp)]

# "Spatial interpolation": Get distances between block group centroids and all survey responses
# then calculate distance-weighted average of the block groups
matrix = np.zeros([len(bgs_area_gdf), len(gdf)])

for i in np.arange(len(bgs_area_gdf)):
    for j in np.arange(len(gdf)):
        matrix[i,j] = hs.haversine((bgs_area_gdf.iloc[i]['LAT'], bgs_area_gdf.iloc[i]['LON']),(gdf.iloc[j]['Latitude'], gdf.iloc[j]['Longitude']))

# each row of matrix is a block group, each column is that block group's distance to a different survey response
avg = np.zeros([len(bgs_area_gdf)])

for i in np.arange(len(bgs_area_gdf)): # go through all block groups in matrix, taking weighted average of them
    avg[i] = np.average(survey['Distance'], weights = 1/matrix[i])

survey_distance_dict = {list(bgs_area_gdf['GISJOIN'])[i]: avg[i] for i in range(len(avg))}
