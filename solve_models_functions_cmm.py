# Will be three modeling steps:
# Model inputs: State budget, max travel distance
# 1. Demand maximation (s/t cost, distance), gives # people we can route to a hub
# 2. Aggregate distance minimization
# 3. Use (x) * # people, (y) * distance for cost minimization

import os
from datetime import datetime
import pandas as pd
import numpy as np
from pyomo.environ import *
import pyomo.opt as pyopt

import geopandas as gpd
import pandas as pd
import numpy as np
from statistics import mean

import itertools

import matplotlib.pyplot as plt
import plotly.express as px
import shapely
import folium
import plotly.graph_objects as go # or plotly.express as px
import seaborn as sns

from data_cleaning_cmm import (blockgroup_pop_dict, blockgroup_walkability_dict, blockgroup_no_car_pop_dict, bg_ces_dict,
                               dist_to_site_contra_costa_df, dist_to_site_contra_costa_dict,
                               dist_to_site_contra_costa_walk_df, dist_to_site_contra_costa_walk_dict,
                               dist_to_site_wilmington_df, dist_to_site_wilmington_dict,
                               dist_to_site_wilmington_walk_df, dist_to_site_wilmington_walk_dict,
                           county_prop_ealp_dict, site_kw_occ_dict,
                           site_sqft_dict, site_cost_dict)

import deployment_models_cmm
import importlib
importlib.reload(deployment_models_cmm)

# Demand maximization s/t budget, with optional distance, CES score incorporation, and use of the walking population rather than total population
def model_pop_served_max(dist_to_site_df, max_cost, max_distance = 10000000, CES = False, walk_pop = False):
    # Set up base model
    #     # Set up base model
    #     model_base, bg_with_no_hub = deployment_models_cmm.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, blockgroup_walkability_dict, dist_to_site_df)
    #     model_dict = dict()
    if walk_pop == False:
        model_base, bg_with_no_hub = deployment_models_cmm.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, blockgroup_walkability_dict, dist_to_site_df)
    else:
        model_base, bg_with_no_hub = deployment_models_cmm.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_no_car_pop_dict, bg_ces_dict, blockgroup_walkability_dict, dist_to_site_df)
    model_dict = dict()

    # Demand maximization objective and constraint for total cost and to meet defined proportion of total population
    model_key = "demand_max"
    model_dict[model_key] = model_base.clone()
    model_dict[model_key] = deployment_models_cmm.constrain_total_cost(model_dict[model_key],max_cost)

    if CES == False:
        model_dict[model_key] = deployment_models_cmm.add_demand_maximization_objective(model_dict[model_key], max_distance)
    else:
        model_dict[model_key] = deployment_models_cmm.add_weighted_demand_maximization_objective(model_dict[model_key], max_distance)

    results = SolverFactory('gurobi').solve(model_dict[model_key])

    var_hub_yn, var_bg_pop, var_prop_served, var_distance_matrix = deployment_models_cmm.get_variables_from_model(model_dict[model_key])

    return var_hub_yn

# # Demand maximization s/t budget
# ######### Basic demand maximization #############
# def model_demand_max(max_cost, prop_served_scale_factor, model_dict, model_base):
#     # Demand maximization objective and constraint for total cost and to meet defined proportion of total population
#     model_key = "demand_max"
#     model_dict[model_key] = model_base.clone()
#     model_dict[model_key] = deployment_models_cmm.constrain_total_cost(model_dict[model_key],max_cost)
#     model_dict[model_key] = deployment_models_cmm.add_demand_maximization_objective(model_dict[model_key])
#     results = SolverFactory('gurobi').solve(model_dict[model_key])
#     #print(results)
#     var_hub_yn, var_bg_pop, var_prop_served, var_distance_matrix = deployment_models_cmm.get_variables_from_model(model_dict[model_key])
#
#     # Calculate number of people served
#     num_served_bg = var_prop_served.sum(axis = 1)*var_bg_pop['POPULATION']
#     prop_served = sum(num_served_bg.loc[num_served_bg != 0])/sum(var_bg_pop['POPULATION'])
#     scaled_prop_served = prop_served * prop_served_scale_factor
#     return scaled_prop_served
#
# ######### Basic p median #############
# def model_p_median(max_cost, scaled_prop_served, agg_dist_scale_factor, model_dict, model_base):
#     # p median objective and constraint for total cost and to meet defined proportion of total population
#     model_key = "p_median"
#     model_dict[model_key] = model_base.clone()
#     model_dict[model_key] = deployment_models_cmm.constrain_total_cost(model_dict[model_key],max_cost)
#     model_dict[model_key] = deployment_models_cmm.constrain_min_total_pop(model_dict[model_key],scaled_prop_served)
#     model_dict[model_key] = deployment_models_cmm.add_p_median_objective(model_dict[model_key])
#     results = SolverFactory('gurobi').solve(model_dict[model_key])
#     #print(results)
#     var_hub_yn, var_bg_pop, var_prop_served, var_distance_matrix = deployment_models_cmm.get_variables_from_model(model_dict[model_key])
#
#     # Create set of blockgroup, site pairs within five miles of each other
#     def filter_to_nearby_sites(bg, site):
#         return not np.isnan(var_distance_matrix.loc[bg, site])
#
#     bg_site_pairs = list(itertools.product(var_distance_matrix.columns,var_distance_matrix.index))
#     bg_site_pairs = [x for x in bg_site_pairs if filter_to_nearby_sites(x[1], x[0])]
#
#     # Calculate aggregate distance and scaled aggregated distance
#     agg_dist = sum([var_bg_pop.loc[bg, 'POPULATION'] * var_distance_matrix.loc[bg, site] * var_prop_served.loc[bg, site] for site, bg in bg_site_pairs])
#     scaled_agg_dist = agg_dist * agg_dist_scale_factor
#     return scaled_agg_dist
#
# ######### Walkability weighted p median #############
# def model_p_median_walkability(max_cost, scaled_prop_served, agg_dist_scale_factor, model_dict, model_base):
#     # p median objective and constraint for total cost and to meet defined proportion of total population
#     model_key = "p_median"
#     model_dict[model_key] = model_base.clone()
#     model_dict[model_key] = deployment_models_cmm.constrain_total_cost(model_dict[model_key],max_cost)
#     model_dict[model_key] = deployment_models_cmm.constrain_min_total_pop(model_dict[model_key],scaled_prop_served)
#     model_dict[model_key] = deployment_models_cmm.add_p_median_objective_walkability(model_dict[model_key])
#     results = SolverFactory('gurobi').solve(model_dict[model_key])
#     #print(results)
#     var_hub_yn, var_bg_pop, var_prop_served, var_distance_matrix = deployment_models_cmm.get_variables_from_model(model_dict[model_key])
#
#     # Create set of blockgroup, site pairs within five miles of each other
#     def filter_to_nearby_sites(bg, site):
#         return not np.isnan(var_distance_matrix.loc[bg, site])
#
#     bg_site_pairs = list(itertools.product(var_distance_matrix.columns,var_distance_matrix.index))
#     bg_site_pairs = [x for x in bg_site_pairs if filter_to_nearby_sites(x[1], x[0])]
#
#     # Calculate aggregate distance and scaled aggregated distance
#     agg_dist = sum([var_bg_pop.loc[bg, 'POPULATION'] * var_distance_matrix.loc[bg, site] * var_prop_served.loc[bg, site] for site, bg in bg_site_pairs])
#     scaled_agg_dist = agg_dist * agg_dist_scale_factor
#     return scaled_agg_dist
#
# ######### Cost Minimization #############
# # cost minimization objective and constraints for aggregate distance and proportion of the population served
# # returns dataframe of whether or not hubs were built and objective value (cost to build)
# def model_min_cost(scaled_agg_dist, scaled_prop_served, model_dict, model_base):
#     model_key = "cost"
#     model_dict[model_key] = model_base.clone()
#     model_dict[model_key] = deployment_models_cmm.constrain_maximum_agg_distance(model_dict[model_key],scaled_agg_dist)
#     model_dict[model_key] = deployment_models_cmm.constrain_min_total_pop(model_dict[model_key],scaled_prop_served)
#     model_dict[model_key] = deployment_models_cmm.add_cost_minimzation_objective(model_dict[model_key])
#     results = SolverFactory('gurobi').solve(model_dict[model_key])
#     #print(results)
#     obj_val = model_dict[model_key].obj_cost_minimzation()
#     var_hub_yn, var_bg_pop, var_prop_served, var_distance_matrix = deployment_models_cmm.get_variables_from_model(model_dict[model_key])
#     return var_hub_yn, obj_val
#
# # cost minimization objective and constraints for aggregate distance and proportion of the population served
# # uses weighted total population constraint based on CES score
# # returns dataframe of whether or not hubs were built and objective value (cost to build)
# def model_min_cost_ces(scaled_agg_dist, scaled_prop_served, min_prop_ej, ej_cutoff, model_dict, model_base):
#     model_key = "cost"
#     model_dict[model_key] = model_base.clone()
#     model_dict[model_key] = deployment_models_cmm.constrain_maximum_agg_distance(model_dict[model_key],scaled_agg_dist)
#     model_dict[model_key] = deployment_models_cmm.prioritize_CES(model_dict[model_key],min_prop_ej,ej_cutoff) # must serve min_prop_ej prop for BG with CES scores greater than ej_cutoff
#     model_dict[model_key] = deployment_models_cmm.constrain_min_total_pop(model_dict[model_key],scaled_prop_served)
#     model_dict[model_key] = deployment_models_cmm.add_cost_minimzation_objective(model_dict[model_key])
#     results = SolverFactory('gurobi').solve(model_dict[model_key])
#     #print(results)
#     obj_val = model_dict[model_key].obj_cost_minimzation()
#     var_hub_yn, var_bg_pop, var_prop_served, var_distance_matrix = deployment_models_cmm.get_variables_from_model(model_dict[model_key])
#     return var_hub_yn, obj_val
#
# ######### Cost Minimization from demand maximization and p median #############
# # takes distance to sites dataframe (constrains geometry of interest),
# #    amount we can spend on hubs, miles we can go to a hub, scale factors
# # returns locations of built hubs
# def model_func(dist_to_site_df, max_cost, prop_served_scale_factor, agg_dist_scale_factor, dist = np.nan):
#     # take out everything over the minimum distance (if there is a maximum distance)
#     if(dist == dist):
#         dist_to_site_df[dist_to_site_df > dist] = pd.NA
#
#     # Set up base model
#     model_base, bg_with_no_hub = deployment_models_cmm.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, blockgroup_walkability_dict, dist_to_site_df)
#     model_dict = dict()
#
#     prop_served_output = model_demand_max(max_cost, prop_served_scale_factor, model_dict, model_base)
#     agg_dist_output = model_p_median(max_cost, prop_served_output, agg_dist_scale_factor, model_dict, model_base)
#     return model_min_cost(agg_dist_output, prop_served_output, model_dict, model_base)
#
# # takes distance to sites dataframe (constrains geometry of interest),
# #    amount we can spend on hubs, miles we can go to a hub, scale factors
# # uses CES constraint -- way this works now is you have to meet 50% of the demand model output (which is scaled via scale factor)
# #    and 125% of the scaled demand model output in BGs over CES 80th percentile
# # returns locations of built block groups
# def model_func_ces(dist_to_site_df, max_cost, prop_served_scale_factor, agg_dist_scale_factor, dist = np.nan):
#     # take out everything over the minimum distance (if there is a maximum distance)
#     if(dist == dist):
#         dist_to_site_df[dist_to_site_df > dist] = pd.NA
#
#     # Set up base model
#     model_base, bg_with_no_hub = deployment_models_cmm.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, blockgroup_walkability_dict, dist_to_site_df)
#     model_dict = dict()
#
#     prop_served_output = model_demand_max(max_cost, prop_served_scale_factor, model_dict, model_base)
#     agg_dist_output = model_p_median(max_cost, prop_served_output, agg_dist_scale_factor, model_dict, model_base)
#     return model_min_cost_ces(agg_dist_output, prop_served_output*.50, prop_served_output*1.25, .8, model_dict, model_base)
#
# # takes distance to sites dataframe (constrains geometry of interest),
# #    amount we can spend on hubs, miles we can go to a hub, scale factors
# # returns locations of built hubs
# def model_func_walkability(dist_to_site_df, max_cost, prop_served_scale_factor, agg_dist_scale_factor, dist = np.nan):
#     # take out everything over the minimum distance (if there is a maximum distance)
#     if(dist == dist):
#         dist_to_site_df[dist_to_site_df > dist] = pd.NA
#
#     # Set up base model
#     model_base, bg_with_no_hub = deployment_models_cmm.build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, blockgroup_walkability_dict, dist_to_site_df)
#     model_dict = dict()
#
#     prop_served_output = model_demand_max(max_cost, prop_served_scale_factor, model_dict, model_base)
#     agg_dist_output = model_p_median_walkability(max_cost, prop_served_output, agg_dist_scale_factor, model_dict, model_base)
#     return model_min_cost(agg_dist_output, prop_served_output, model_dict, model_base)

# function that takes resilience hub or block group data and id,
# and returns coordinates of hub or block group corresponding to id
def locate(data, id, col):
    row = data.loc[data[col] == id]
    return [row['LAT'].iloc[0], row['LON'].iloc[0]]

# Map hub locations based on built_yn
def map_hubs(built_yn, site_data):
    sites = pd.DataFrame(columns = ['LAT', 'LON'])
    hubs = built_yn.loc[built_yn['BUILT'] == 1].index
    for site in hubs:
        site_pt = locate(site_data, site, 'id_site')
        sites.loc[len(sites.index)] = site_pt
    fig = px.scatter_mapbox(lat=sites['LAT'], lon=sites['LON'], mapbox_style="open-street-map", zoom=10, color_discrete_sequence = ["black"])
    fig.show()

# function that takes distance matrix and hub ids, and outputs list of block
# groups that don't have a distance less than max_distance to one of the built hubs
def no_distance(hub_ids, distances, max_distance):
    filtered = distances[hub_ids]
    filtered = filtered.where(filtered < max_distance, None)
    #print(list(filtered[~filtered.isnull().all(axis=1)].max(axis = 1)))
    return filtered[filtered.isnull().all(axis=1)].index

# function that takes distance matrix and hub ids, and outputs list of block
# groups that do have a distance less than max_distance to one of the built hubs
def yes_distance(hub_ids, distances, max_distance):
    filtered = distances[hub_ids]
    filtered = filtered.where(filtered < max_distance, None)
    #print(list(filtered[~filtered.isnull().all(axis=1)].max(axis = 1)))
    return filtered[~filtered.isnull().all(axis=1)].index

# function that takes distance matrix and hub ids, and outputs dataframe of bg id and
# closest hub id under max_distance away, with bgs without a hub under max_distance away
# not included
def get_closest_hubs(hub_ids, distances, max_distance):
    filtered = distances[hub_ids]
    filtered.where(filtered < max_distance, None, inplace=True)
    distances = filtered[~filtered.isnull().all(axis=1)].idxmin(axis = 1)
    return pd.DataFrame(data = distances, columns = ['site_id'])

# function that returns list of passed characteristic in passed data frame
# for passed list of block group ids
def retrieve_characteristics(hub_ids, data, characteristic):
    return data.loc[data['GISJOIN'].isin(list(hub_ids))][characteristic]

# function that takes an array of arrays of block group ids, data (from CES), group names,
# and a desired characteristic and creates a boxplot
def boxplot_characteristics(list_bg_ids, data, group_names, characteristic):
    list_x = [[]]*len(list_bg_ids)
    # create x values for plot
    for i in np.arange(len(list_bg_ids)):
        list_x[i] = (retrieve_characteristics(list_bg_ids[i], data, characteristic))

    plt.boxplot(list_x, labels = group_names);
    plt.ylabel(characteristic)
    return(plt)

# function that takes an array of arrays of block group ids, data (from CES), group names,
# and a desired characteristic and creates a histogram
def histogram_characteristics(list_bg_ids, data, group_names, characteristic):
    list_x = pd.DataFrame(columns = [characteristic, 'Key'])
    # create x values for plot
    for i in np.arange(len(list_bg_ids)):
        to_append = pd.DataFrame({characteristic: (retrieve_characteristics(list_bg_ids[i], data, characteristic)),
                              'Key': [group_names[i]]*len(list_bg_ids[i])})
        list_x = pd.concat([list_x, to_append])
    list_x.reset_index(level=0, inplace=True)
    fig = sns.kdeplot(x = list_x[characteristic],
                  hue = list_x['Key'],
                  common_norm = True)
    sns.move_legend(fig, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
