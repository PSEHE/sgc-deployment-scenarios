"""
After a model is run, we want to quickly collect statistics from it.
These are the things we might want to know...
1. Average distance?
2. Average distance for EJ/not-EJ populations?
3. Total demand met?
4. Total EJ/not-EJ demand met?
5. Number of hubs built?
6. Capacities of hub
7. Hub dictionary of
    a. Number of people going to hub
    b. Capacity of hub
    c. Cost of hub
    d. Average distance people travel to hub
    e. List of distances people trael to get to hub (maybe not bother)
    f. Type of hub

8. BG dictionary of
    a. Number of people in blockgroup
    b. EJ score
    c. Number of people that have a site to go to
    d. Dictionary of distances that people have to travel (maybe not bother)
    e. Average distance that people have to travel
    f. Distance to nearest hub
9. Total money spent
"""
# COST MINIMIZATION MODELS
# %%codecell
import os
from datetime import datetime
import pandas as pd
import geopandas as gpd
import geopandas as gpd
import numpy as np
from pyomo.environ import *
import pyomo.opt as pyopt
import numpy as np
from data_cleaning_cmm import blockgroup_pop_dict, bg_ces_dict,county_prop_ealp_dict,site_kw_occ_dict,site_sqft_dict, site_cost_dict
site_costs = [cost for cost in site_cost_dict.values()]
import deployment_models
import vulnerability_risk_functions
import importlib

from gurobipy import *

# %% codecell
ca_county_names = [ \
                    'Alameda', 'Alpine', 'Amador', 'Butte', 'Calaveras', 'Colusa', 'Contra Costa',
                   'Del Norte', 'El Dorado', 'Fresno', 'Glenn', 'Humboldt', 'Imperial', 'Inyo',
                   'Kern', 'Kings', 'Lake', 'Lassen', 'Los Angeles', 'Madera', 'Marin', 'Mariposa',
                   'Mendocino', 'Merced', 'Modoc', 'Mono', 'Monterey', 'Napa', 'Nevada', 'Orange',
                   'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
                   'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
                   'Santa Barbara', 'Santa Clara','Santa Cruz','Shasta', 'Sierra', 'Siskiyou',
                   'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
                   'Tuolumne','Ventura', 'Yolo', 'Yuba'
                   ]


ca_county_fips = ['00' + str(int(num)) for num in np.linspace(1, 115, 58)]
ca_county_fips = [num[-3:] for num in ca_county_fips]
ca_counties = {ca_county_names[i]:ca_county_fips[i] for i in range(len(ca_county_names))}
ca_counties_subset = [ \
#                         'Alameda', 'Alpine', 'Amador', 'Butte',
#                         'Calaveras', 'Colusa',
                      'Contra Costa',
#                         'Del Norte', 'El Dorado',
#                         'Fresno',
#                         'Glenn',
#                         'Humboldt', 'Imperial', 'Inyo',
#                         'Kern', 'Kings', 'Lake', 'Lassen',
#                         'Los Angeles',
#                         'Madera', 'Marin', 'Mariposa',
#                         'Mendocino', 'Merced', 'Modoc', 'Mono',
#                         'Monterey', 'Napa', 'Nevada', 'Orange',
#                         'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
#                         'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
#                         'Santa Barbara', 'Santa Clara','Santa Cruz','Shasta', 'Sierra', 'Siskiyou',
#                         'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
#                         'Tuolumne','Ventura', 'Yolo', 'Yuba'
                        ]
ca_counties = {county: ca_counties[county] for county in ca_counties_subset}

# %% markdown
# # Define parameters
# %% codecell
california_budget = 1*10**9
min_service_fraction_multiplier = 0.75
distance_cutoff_demand_maximization = 3
min_distance = 0.5
max_blockgroup_service_fraction = 0.4
# max_blockgroup_service_fraction = bg_ces_dict

# %% markdown
# # Analysis loop
# %% codecell


cost_objective_dict = dict()
dist_to_site_df_dict = dict()

# min_service_fractions = [0.05,0.1,0.15,0.2]
# average_distances = [1,2,3]

min_service_fractions = [0.25]
average_distances = [1]
min_prop_ej = 0.25
ej_cutoff = 0.5

# minimize cost s/t CES prioritization, serving the minimum fraction of people across CA, max distance away
for county, county_fips in ca_counties.items():

    dist_to_site_df = pd.read_csv(os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_' + county.lower().replace(' ', '') + '.csv'),index_col = 0)
    dist_to_site_df_dict[county_fips] = dist_to_site_df
    # INSERT CODE TO DROP COLUMNS IF SITE IS NOT IN site_kw_occ_dict
    sites_to_drop = [site for site in dist_to_site_df.columns if not(site in site_kw_occ_dict.keys())]
    dist_to_site_df.drop(columns = sites_to_drop,inplace=True)
    model_base, bg_with_no_hub = deployment_models.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, dist_to_site_df)
    total_pop = sum([model_base.param_bg_pop[bg] for bg in model_base.idx_bgs])
    for min_service_fraction in min_service_fractions:
        for average_distance in average_distances:
            model = model_base.clone()
            model = deployment_models.constrain_min_total_pop(model,min_service_fraction)
            model = deployment_models.constrain_maximum_agg_distance(model,average_distance*min_service_fraction*total_pop)
            model = deployment_models.prioritize_CES(model,min_prop_ej,ej_cutoff)
            model = deployment_models.add_cost_minimzation_objective(model)

            results = SolverFactory('gurobi').solve(model)

            cost_objective_dict[(min_service_fraction,average_distance)] = value(model.obj_cost_minimzation)
            print(results)
            # var_hub_yn, var_prop_served = deployment_models.get_vars(model_dict[model_key])


# %%codecell



# %%codecell

import matplotlib.pyplot as plt

importlib.reload(vulnerability_risk_functions)
importlib.reload(deployment_models)
# def find_nearest_built_hub(distance_matrix, hub_df, bg_df):
#     built_hubs = hubs_df.index[hubs_df["BUILT"]==1]
#     unbuilt_hubs = hubs_df.index[hubs_df["BUILT"]==0]
#     for bg in bg_df.index:
#         nearest_hub = distance_matrix[built_hubs]
#     return nearest_hub_series

def model_stats(model,vulnerability_column = "SCORE_PCTL_CI_BG"):

    hubs_df, bgs_df, prop_served, distance_matrix = deployment_models.get_variables_from_model(model)
    built_hubs = hubs_df.index[hubs_df["BUILT"]==1]
    GISJOIN = [bg for bg in model.idx_bgs.value]
    vulnerability_df = vulnerability_risk_functions.get_vulnerability_data(GISJOIN,data_source = "CalEnviroScreen_blockgroup",
                            vulnerability_column = vulnerability_column)
    vulnerability_df["IS_VULNERABLE"] = vulnerability_df[vulnerability_column]>=75

    bgs_df = bgs_df.join(vulnerability_df[[vulnerability_column,"IS_VULNERABLE"]])
    np.unique(distance_matrix[built_hubs].min(axis=1))
    bgs_df["HAS_HUB"] = False
    bgs_df["DISTANCE"] = np.NaN

    hubs_df["SERVICE_POPULATION"] = 0
    hubs_df["SERVICE_POPULATION_VULNERABLE"] = 0
    hubs_df["TOTAL_DISTANCE"] = 0
    hubs_df["TOTAL_VULNERABILITY"] = 0
    hubs_df["TOTAL_DISTANCE_VULNERABLE"] = 0
    hubs_df["TOTAL_DISTANCE_TIMES_VULNERABILITY"] = 0
    missing_population = 0
    for bg_idx,row in distance_matrix.iterrows():
        # nearest_hub = distance_matrix[built_hubs].min(axis=1)
        nearest_hub_distance = row[built_hubs].min()
        if ~np.isnan(nearest_hub_distance):
            bgs_df.loc[bg_idx,"DISTANCE"] = nearest_hub_distance
            bgs_df.loc[bg_idx,"HAS_HUB"] = True
            nearest_hub = row[built_hubs].idxmin()
            hubs_df.loc[nearest_hub,"SERVICE_POPULATION"] += bgs_df.loc[bg_idx,"POPULATION"]
            hubs_df.loc[nearest_hub,"TOTAL_DISTANCE"] += bgs_df.loc[bg_idx,"POPULATION"]*nearest_hub_distance
            hubs_df.loc[nearest_hub,"TOTAL_VULNERABILITY"] += bgs_df.loc[bg_idx,"POPULATION"]*bgs_df.loc[bg_idx,vulnerability_column]
            if bgs_df.loc[bg_idx,"IS_VULNERABLE"]:
                hubs_df.loc[nearest_hub,"SERVICE_POPULATION_VULNERABLE"] += bgs_df.loc[bg_idx,"POPULATION"]
                hubs_df.loc[nearest_hub,"TOTAL_DISTANCE_VULNERABLE"] += bgs_df.loc[bg_idx,"POPULATION"]*nearest_hub_distance
            # hubs_df.loc[nearest_hub,"TOTAL_DISTANCE_VULNERABLE"] =
        else:
            bgs_df.loc[bg_idx,"DISTANCE"] = row.max()
            bgs_df.loc[bg_idx,"HAS_HUB"] = False
            missing_population += bgs_df.loc[bg_idx,"POPULATION"]
        hubs_df[hubs_df["BUILT"]==True]

    # hubs_df["SERVICE_POPULATION"].sum()
    # bgs_df["DISTANCE"].mean()
    # np.sum(~np.isnan(distance_matrix[built_hubs].min(axis=1)))

    return bgs_df, hubs_df, prop_served,distance_matrix
















# # %%codecell
# california_budget = 1*10**9
# min_service_fraction_multiplier = 0.75
# distance_cutoff_demand_maximization = 3
# min_distance = 0.5
# max_blockgroup_service_fraction = 0.4
# # max_blockgroup_service_fraction = bg_ces_dict
#
# # %% markdown
# # # Analysis loop
# # %% codecell
# import deployment_models
# import importlib
# importlib.reload(deployment_models)
#
# cost_objective_dict = dict()
# dist_to_site_df_dict = dict()
#
# # min_service_fractions = [0.05,0.1,0.15,0.2]
# # average_distances = [1,2,3]
#
# min_service_fractions = [0.2,0.3,0.4]
# average_distances = [2]
# min_prop_ej = 0.25
# ej_cutoff = 0.5
#
# model_dict = dict()
# cost_dict = dict()
# hubs_df_dict = dict()
# bgs_df_dict = dict()
# for county, county_fips in ca_counties.items():
#
#     dist_to_site_df = pd.read_csv(os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_' + county.lower().replace(' ', '') + '.csv'),index_col = 0)
#     dist_to_site_df_dict[county_fips] = dist_to_site_df
#     sites_to_drop = [site for site in dist_to_site_df.columns if not(site in site_kw_occ_dict.keys())]
#     dist_to_site_df.drop(columns = sites_to_drop,inplace=True)
#     model_base, bg_with_no_hub = deployment_models.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, dist_to_site_df)
#     total_pop = sum([model_base.param_bg_pop[bg] for bg in model_base.idx_bgs])
#     for min_service_fraction in min_service_fractions:
#         # for average_distance in average_distances:
#         model = model_base.clone()
#         model = deployment_models.constrain_min_total_pop(model,min_service_fraction)
#         model = deployment_models.constrain_maximum_agg_distance(model,average_distance*min_service_fraction*total_pop)
#         model = deployment_models.prioritize_CES(model,min_prop_ej,ej_cutoff)
#         model = deployment_models.add_cost_minimzation_objective(model)
#         results = SolverFactory('gurobi').solve(model)
#
#         bgs_df, hubs_df, prop_served,distance_matrix = model_stats(model)
#         model_dict[min_service_fraction] = model
#         cost_dict[min_service_fraction] = value(model.obj_cost_minimzation)
#         hubs_df_dict[min_service_fraction] = hubs_df
#         bgs_df_dict[min_service_fraction] = bgs_df
#         # cost_objective_dict[(min_service_fraction,average_distance)] = value(model.obj_cost_minimzation)
#         print(results)
#
#
#
# # %%codecell
#
# bgs_df
# import matplotlib.pyplot as plt
# import plotly.express as px
#
# # %%codecell
# fig,axs = plt.subplots(len(min_service_fractions),figsize = (8,8))
# bins = np.arange(0,50,4)
# y_max = 45
# for (idx,min_service_fraction) in zip(range(len(min_service_fractions)),min_service_fractions):
#     hubs_df = hubs_df_dict[min_service_fraction]
#     hubs_df_built = hubs_df.loc[hubs_df["BUILT"]==True].copy()
#     hubs_df_built["CAPACITY_RATIO"] = hubs_df_built["SERVICE_POPULATION"]/hubs_df_built["CAPACITY"]
#
#     hubs_df_built["CAPACITY_RATIO"].hist(ax = axs[idx],bins = bins)
#     axs[idx].set_ylim((0,y_max))
#     axs[idx].set_title(str(round(cost_dict[min_service_fraction]/1000000))+ " million dollars")
#     axs[idx].set_ylabel("Number of hubs")
#     axs[idx].set_xlabel("Service Population/Capacity")
# plt.tight_layout()
# # %%codecell
# fig,axs = plt.subplots(len(min_service_fractions),figsize = (8,8))
# bins = np.arange(0,50,4)
# y_max = 45
# for (idx,min_service_fraction) in zip(range(len(min_service_fractions)),min_service_fractions):
#     hubs_df = hubs_df_dict[min_service_fraction]
#     hubs_df_built = hubs_df.loc[hubs_df["BUILT"]==True].copy()
#     hubs_df_built["VULNERABILITY_AVERAGE"] = hubs_df_built["TOTAL_VULNERABILITY"]/hubs_df_built["SERVICE_POPULATION"]
#     hubs_df_built["DISTANCE_AVERAGE"] = hubs_df_built["TOTAL_DISTANCE"]/hubs_df_built["SERVICE_POPULATION"]
#
#     axs[idx].scatter(hubs_df_built["VULNERABILITY_AVERAGE"],hubs_df_built["DISTANCE_AVERAGE"])
#     # axs[idx].set_ylim((0,y_max))
#     axs[idx].set_title(str(round(cost_dict[min_service_fraction]/1000000))+ " million dollars")
#     axs[idx].set_ylabel("Average Travel Distance")
#     axs[idx].set_xlabel("Average Vulnerability")
# plt.tight_layout()
#
# # %%codecell
# import deployment_models
# import importlib
# importlib.reload(deployment_models)
#
# cost_objective_dict = dict()
# dist_to_site_df_dict = dict()
#
# # min_service_fractions = [0.05,0.1,0.15,0.2]
# # average_distances = [1,2,3]
#
# min_service_fractions = [0.3]
# average_distances = [2]
# min_prop_ejs = [0.0,0.2,0.4,0.6]
# ej_cutoff = 0.25
#
# model_dict = dict()
# cost_dict = dict()
# hubs_df_dict = dict()
# bgs_df_dict = dict()
# for county, county_fips in ca_counties.items():
#
#     dist_to_site_df = pd.read_csv(os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_' + county.lower().replace(' ', '') + '.csv'),index_col = 0)
#     dist_to_site_df_dict[county_fips] = dist_to_site_df
#     sites_to_drop = [site for site in dist_to_site_df.columns if not(site in site_kw_occ_dict.keys())]
#     dist_to_site_df.drop(columns = sites_to_drop,inplace=True)
#     model_base, bg_with_no_hub = deployment_models.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, dist_to_site_df)
#     total_pop = sum([model_base.param_bg_pop[bg] for bg in model_base.idx_bgs])
#     for min_prop_ej in min_prop_ejs:
#         # for average_distance in average_distances:
#         model = model_base.clone()
#         model = deployment_models.constrain_min_total_pop(model,min_service_fraction)
#         model = deployment_models.constrain_maximum_agg_distance(model,average_distance*min_service_fraction*total_pop)
#         model = deployment_models.prioritize_CES(model,min_prop_ej,ej_cutoff)
#         model = deployment_models.add_cost_minimzation_objective(model)
#         results = SolverFactory('gurobi').solve(model)
#
#         bgs_df, hubs_df, prop_served,distance_matrix = model_stats(model)
#         model_dict[min_prop_ej] = model
#         cost_dict[min_prop_ej] = value(model.obj_cost_minimzation)
#         hubs_df_dict[min_prop_ej] = hubs_df
#         bgs_df_dict[min_prop_ej] = bgs_df
#         # cost_objective_dict[(min_service_fraction,average_distance)] = value(model.obj_cost_minimzation)
#         print(results)
#
# fig,axs = plt.subplots(len(min_prop_ejs),figsize = (8,8))
# bins = np.arange(0,50,4)
# y_max = 45
# for (idx,min_prop_ej) in zip(range(len(min_prop_ejs)),min_prop_ejs):
#     hubs_df = hubs_df_dict[min_prop_ej]
#     hubs_df_built = hubs_df.loc[hubs_df["BUILT"]==True].copy()
#     hubs_df_built["VULNERABILITY_AVERAGE"] = hubs_df_built["TOTAL_VULNERABILITY"]/hubs_df_built["SERVICE_POPULATION"]
#     hubs_df_built["DISTANCE_AVERAGE"] = hubs_df_built["TOTAL_DISTANCE"]/hubs_df_built["SERVICE_POPULATION"]
#
#     axs[idx].scatter(hubs_df_built["VULNERABILITY_AVERAGE"],hubs_df_built["DISTANCE_AVERAGE"])
#     # axs[idx].set_ylim((0,y_max))
#     axs[idx].set_title(str(round(cost_dict[min_prop_ej]/1000000))+ " million dollars")
#     axs[idx].set_ylabel("Average Travel Distance")
#     axs[idx].set_xlabel("Average Vulnerability")
# plt.tight_layout()
#
#
# # %%codecell
# fig,axs = plt.subplots(len(min_prop_ejs),figsize = (8,10))
# bins = np.arange(0,50,4)
# y_max = 45
# for (idx,min_prop_ej) in zip(range(len(min_prop_ejs)),min_prop_ejs):
#     hubs_df = hubs_df_dict[min_prop_ej]
#     hubs_df_built = hubs_df.loc[hubs_df["BUILT"]==True].copy()
#     hubs_df_built["VULNERABILITY_AVERAGE"] = hubs_df_built["TOTAL_VULNERABILITY"]/hubs_df_built["SERVICE_POPULATION"]
#     hubs_df_built["DISTANCE_AVERAGE"] = hubs_df_built["TOTAL_DISTANCE"]/hubs_df_built["SERVICE_POPULATION"]
#     hubs_df_built["CAPACITY_RATIO"] = hubs_df_built["SERVICE_POPULATION"]/hubs_df_built["CAPACITY"]
#     axs[idx].scatter(hubs_df_built["VULNERABILITY_AVERAGE"],hubs_df_built["CAPACITY_RATIO"])
#     axs[idx].set_ylim((0,y_max))
#     axs[idx].set_title(str(round(cost_dict[min_prop_ej]/1000000))+ " million dollars")
#     axs[idx].set_ylabel("Service Fraction/Capacity")
#     axs[idx].set_xlabel("Average Vulnerability")
# plt.tight_layout()
#
#
#
#
#
# # %%codecell
#
# # %%codecell
#
#
#
#
# total_vulnerable_pop = [np.sum(bg_df_dict.loc[(bg_df["IS_VULNERABLE"])&(bg_df["HAS_HUB"])]) for bg_df in bgs_df_dict]
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# ####################################################
# # BLOCKGROUP TOTAL DEMAND MET HISTOGRAMS
# EJ_bg = [bg for bg in var_prop_served.index if bg in bg_ces_df[bg_ces_df["SCORE_PCTL_CI_BG"]>=75]["GISJOIN"].to_list()]
# not_EJ_bg = [bg for bg in var_prop_served.index if bg in bg_ces_df[bg_ces_df["SCORE_PCTL_CI_BG"]<75]["GISJOIN"].to_list()]
#
# axs[0,0].hist([var_prop_served.loc[EJ_bg].sum(axis=1),
#                 var_prop_served.loc[not_EJ_bg].sum(axis=1)],
#                 label = ("Calenviroscreen>=75","Calenviroscreen<75"),
#                 stacked=True, # histtype=u'step'
#                 )
# axs[0,0].legend(fontsize = 8)
# axs[0,0].set_xlabel("Fraction of population served")
# axs[0,0].set_ylabel("Number of blockgroups")
#
# ####################################################
# # CDF OF HUB CAPCITIES
# axs[0,1].hist([hub_occ_dict[hub] for hub in hubs_built], density=True, cumulative=True, label='Built hubs',histtype='step', alpha=0.8)
# axs[0,1].hist([hub_occ_dict[hub] for hub in hubs_not_built], density=True, cumulative=True, label='Unbuilt hubs',histtype='step', alpha=0.8)
# axs[0,1].legend(loc='lower right')
# axs[0,1].set_xlabel("Hub capacity")
# axs[0,1].set_ylabel("Cumulative Probability")
# plt.tight_layout()
#
# ####################################################
# # Calenviroscreen percentiles
# total_fraction_demand_met = var_prop_served.sum(axis=1)
# total_fraction_demand_met.rename("total_fraction_demand_met",inplace=True)
# blockgroup_df_local = blockgroup_df_local.merge(total_fraction_demand_met,left_index=True,right_index=True)
# score_dict = dict()
# score_dict["average_score"] = np.sum(blockgroup_df_local["SCORE_PCTL_CI_BG"]*(blockgroup_df_local["BLOCKGROUPPOP19"]/np.sum(blockgroup_df_local["BLOCKGROUPPOP19"])))
# score_dict["demand_met_score"] = np.sum(blockgroup_df_local["SCORE_PCTL_CI_BG"]*((blockgroup_df_local["total_fraction_demand_met"]*blockgroup_df_local["BLOCKGROUPPOP19"])/(np.sum(blockgroup_df_local["total_fraction_demand_met"]*blockgroup_df_local["BLOCKGROUPPOP19"]))))
# axs[0,2].bar(range(len(score_dict)),list(score_dict.values()),tick_label = list(score_dict.keys()))
# axs[0,2].set_ylabel("Calenviroscreen Percentile")
# axs[0,2].tick_params(axis='x', labelrotation= 25,labelsize=6)
#
# ####################################################
# # Distance travelled
# dist_list = []
# pop_list = []
# for bg,row in var_prop_served.iterrows():
#     for hub in row[row>0].index:
#         dist_list.append(distmatrix_df.loc[bg,hub])
#         pop_list.append(cengeo_pop_dict[bg]*var_prop_served.loc[bg,hub])
#
# axs[1,0].hist(dist_list,weights = pop_list)
# axs[1,0].set_ylabel("Number of people")
# axs[1,0].set_xlabel("Distance_traveled")
#
# ####################################################
# # People per hub
# hub_pop_list = []
# for hub,row in var_prop_served.iteritems():
#     pop = 0
#     for bg in row[row>0].index:
#         pop+=cengeo_pop_dict[bg]*var_prop_served.loc[bg,hub]
#     if pop>0:
#         hub_pop_list.append(pop)
#
# axs[1,1].hist(hub_pop_list)
# axs[1,1].set_ylabel("Number of built hubs")
# axs[1,1].set_xlabel("Number of people")
#
# plt.tight_layout()
# plt.savefig("plots_cost_"+str(max_cost)+"_max_distance"+str(max_distance)+"_ces_"+str(ces_multiplier)+".png")
#
#     # for
