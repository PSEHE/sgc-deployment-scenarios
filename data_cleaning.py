#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import os
import matplotlib.pyplot as plt


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


# ### Create dictionary of hub/blockgroup pairwise distances

# In[4]:


dist_to_site_df = pd.read_csv('data/distmatrix_contracosta.csv')

dist_to_site_dict = {}

for cengeo in dist_to_site_df.index:
    for hub in dist_to_site_df.columns:
        if dist_to_site_df.loc[cengeo, hub] == dist_to_site_df.loc[cengeo, hub]:
            dist_to_site_dict[tuple([cengeo, hub])] = dist_to_site_df.loc[cengeo, hub]


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

people_per_kwh = 0.1

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

# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




