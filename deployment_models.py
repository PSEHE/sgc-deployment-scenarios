import os
from datetime import datetime

import pandas as pd
import numpy as np

from pyomo.environ import *
import pyomo.opt as pyopt

### HERE: CODE TO FILTER EACH OF THE ABOVE TO THE COUNTY OF INTEREST

def build_base_model(site_cost_dict, site_kw_occ_dict, blockgroup_pop_dict, bg_ces_dict, dist_to_site_df):

	##### DEFINE MODEL AND INDICES

	# Create model and initial indices
	model = ConcreteModel()

	model.init_bgs = Set(initialize = dist_to_site_df.index)
	model.init_sites = Set(initialize = dist_to_site_df.columns)

	# Create set of blockgroup, site pairs within five miles of each other
	def filter_to_nearby_sites(model, bg, site):
		return not np.isnan(dist_to_site_df.loc[bg, site])

	model.idx_bg_site_pairs = Set(initialize = model.init_bgs*model.init_sites, filter = filter_to_nearby_sites)

	# Create new index of sites and bgs only including those that belong in <5 mile pair
	filtered_bgs = []
	filtered_sites = []

	for pair in model.idx_bg_site_pairs:
	    if pair[0] not in filtered_bgs:
	        filtered_bgs.append(pair[0])
	    if pair[1] not in filtered_sites:
	        filtered_sites.append(pair[1])

	model.idx_bgs = Set(initialize = filtered_bgs)
	model.idx_sites = Set(initialize = filtered_sites)

	##### DEFINE PARAMETERS

	# Number of people per blockgroup
	def get_blockgroup_pop(model, bg):
		return(blockgroup_pop_dict[bg])

	model.param_bg_pop = Param(model.idx_bgs, initialize = get_blockgroup_pop)

	# Distance from blockgroup to site
	def get_bg_site_dist(model, bg, site):
		return(dist_to_site_df.loc[bg, site])

	model.param_bg_site_dist = Param(model.idx_bg_site_pairs, initialize = get_bg_site_dist)

	# Capacity per site based on kw available
	def get_site_kw_capacity(model, site):
		return(site_kw_occ_dict[site])

	model.param_site_kw_cap = Param(model.idx_sites, initialize = get_site_kw_capacity)

	# Cost per site based on system size
	def get_site_cost(model, site):
		return(site_cost_dict[site])

	model.param_site_cost = Param(model.idx_sites, initialize = get_site_cost)

	# CES Score
	def get_ces_score(model, bg):
		return(bg_ces_dict[bg])

	model.param_bg_vuln_ces = Param(model.idx_bgs, within=Any, default = 0, initialize=get_ces_score)

	# Sites within range for each blockgroup
	bg_sites_in_range = {bg: [] for bg in model.idx_bgs}
	for bg in bg_sites_in_range:
		for pair in model.idx_bg_site_pairs:
			if pair[0] == bg:
				bg_sites_in_range[bg].append(pair[1])

	bg_with_no_hub = [key for key in bg_sites_in_range if len(bg_sites_in_range[key]) == 0]
	for bg in bg_with_no_hub:
		del bg_sites_in_range[bg]

	model.param_bg_sites_in_range = Param(model.idx_bgs, within=Any, initialize=bg_sites_in_range)
	# Blockgroups within range for each site
	site_bgs_in_range = {site: [] for site in model.idx_sites}

	for site in site_bgs_in_range:
		for pair in model.idx_bg_site_pairs:
			if pair[1] == site:
				site_bgs_in_range[site].append(pair[0])
	site_with_no_hub = [key for key in site_bgs_in_range if len(site_bgs_in_range[key]) == 0]

	for site in site_with_no_hub:
		del site_bgs_in_range[site]
	model.param_site_bgs_in_range = Param(model.idx_sites, within=Any, initialize=site_bgs_in_range)

	##### DEFINE VARIABLES
	# Is this site a hub?
	model.var_hub_yn = Var(model.idx_sites, initialize = 1, within = Binary)
	# What proportion of this blockgroup is served at this site?
	model.var_prop_bg_at_site = Var(model.idx_bg_site_pairs, initialize = 1.0, bounds = (0.0, 1.0))
	##### DEFINE CONSTRAINTS

	# Do not serve more people than possible based on kw available at site
	def serve_max_kw_capacity(model, site):
	    site_tot_cap = model.param_site_kw_cap[site]
	    site_tot_served = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for bg in model.param_site_bgs_in_range[site])
	    if model.var_hub_yn[site].value != 1:
	        return((0, site_tot_served, 0))
	    else:
	        return((0, site_tot_served, site_tot_cap))

	model.con_serve_max_kw_capacity = Constraint(model.idx_sites, rule = serve_max_kw_capacity)

	#Do not let anyone go to this site if it is not a hub

	def serve_only_at_hubs(model, bg, site):
		return(model.var_prop_bg_at_site[bg, site] <= model.var_hub_yn[site])

	model.con_serve_only_at_hubs = Constraint(model.idx_bg_site_pairs, rule = serve_only_at_hubs)

	# Do not serve more than 100% of blockgroup demand

	def serve_only_demand(model, bg):
		bg_tot_pop = model.param_bg_pop[bg]
		bg_tot_served = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for site in model.param_bg_sites_in_range[bg])

		return((0, bg_tot_served, bg_tot_pop))

	model.con_serve_only_demand = Constraint(model.idx_bgs, rule = serve_only_demand)

	# Do not send more people to hub than it can fit

	def serve_max_capacity(model, site):
	    site_tot_cap = model.param_site_kw_cap[site]
	    site_tot_served = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for bg in model.param_site_bgs_in_range[site])

	    if model.var_hub_yn[site].value != 1:
	        return((0, site_tot_served, 0))
	    else:
	        return((0, site_tot_served, site_tot_cap))

	model.con_serve_max_capacity = Constraint(model.idx_sites, rule = serve_max_capacity)

	return model, bg_with_no_hub

############################################################
"""
Following are functions to add in constraints and objectives
to the base model that may not be shared across all models
"""

def constrain_min_total_pop(model,min_service_fraction):
	# Serve a minimum proportion of total area population
	pop_area_tot = sum(model.param_bg_pop[bg] for bg in model.idx_bgs)
	pop_service_tot = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs)

	model.con_min_service_pop = Constraint(expr = pop_service_tot >= min_service_fraction*pop_area_tot)

	return model

def constrain_weighted_min_total_pop(model,min_service_fraction):
	# Serve a minimum proportion of total area population
	pop_area_tot = sum(model.param_bg_vuln_ces[bg]*model.param_bg_pop[bg] for bg in model.idx_bgs)
	pop_service_tot = sum(model.param_bg_vuln_ces[bg]*model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs)

	model.con_min_service_pop = Constraint(expr = pop_service_tot >= min_service_fraction*pop_area_tot)

	return model

def constrain_min_blockgroup_pop(model,min_blockgroup_service_fraction):
	# Serve a minimum proportion of each blockgroups population
	# pop_area_tot = sum(model.param_bg_pop[bg] for bg in model.idx_bgs)
	# pop_service_tot = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs)
	model.con_min_blockgroup_service_pop = ConstraintList()
	for idx_bg in model.idx_bgs:
		model.con_min_blockgroup_service_pop.add(expr = sum(model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs if bg==idx_bg) >= min_blockgroup_service_fraction)
	return model

def constrain_max_blockgroup_pop(model,max_blockgroup_service_fraction,max_multiplier = 0.5):
	# Serve a minimum proportion of each blockgroups population
	# pop_area_tot = sum(model.param_bg_pop[bg] for bg in model.idx_bgs)
	# pop_service_tot = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs)
	model.con_max_blockgroup_service_pop = ConstraintList()
	if type(max_blockgroup_service_fraction)==float:
		for idx_bg in model.idx_bgs:
			model.con_max_blockgroup_service_pop.add(expr = sum(model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs if bg==idx_bg) <= max_blockgroup_service_fraction)
		return model
	else:
		for idx_bg in model.idx_bgs:
			model.con_max_blockgroup_service_pop.add(expr = sum(model.var_prop_bg_at_site[bg, site] for bg, site in model.idx_bg_site_pairs if bg==idx_bg) <= max_blockgroup_service_fraction[idx_bg]*max_multiplier)
		return model



# Prioritze CES populations
def prioritize_CES(model,min_prop_ej,ej_cutoff):
	"""
	Minimum proportion of population for blockgroups with CES scores greater than
	ej_cutoff
	"""
	def serve_ces_pops(model, bg):
	    bg_ces_score = model.param_bg_vuln_ces[bg]
	    bg_tot_prop_served = sum(model.var_prop_bg_at_site[bg, site] for site in model.param_bg_sites_in_range[bg])
	    if bg_ces_score >= ej_cutoff:
	        return((min_prop_ej, bg_tot_prop_served, 1))
	    else:
	        return((0, bg_tot_prop_served, 1))
	model.con_serve_ces_pops = Constraint(model.idx_bgs, rule = serve_ces_pops)
	return model

def add_p_median_objective(model):
	##### DEFINE OBJECTIVE
	# Minimize aggregate, population-weighted travel distance
	agg_dist = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site]*model.param_bg_site_dist[bg, site] for bg, site in model.idx_bg_site_pairs)
	model.obj_min_agg_dist = Objective(expr = agg_dist, sense = minimize)
	return model

def constrain_maximum_agg_distance(model,max_agg_distance):
	##### DEFINE OBJECTIVE
	# Minimize aggregate, population-weighted travel distance
	agg_dist = sum(model.param_bg_pop[bg]*model.var_prop_bg_at_site[bg, site]*model.param_bg_site_dist[bg, site] for bg, site in model.idx_bg_site_pairs)
	model.con_max_agg_distance = Constraint(expr = agg_dist<=max_agg_distance)
	return model


def add_demand_maximization_objective(model,max_distance = 10000000):
	##### DEFINE OBJECTIVE
	model.max_coverage = Objective(expr = sum(model.var_prop_bg_at_site[pair]*model.param_bg_pop[pair[0]] for pair in model.idx_bg_site_pairs if model.param_bg_site_dist[pair]<=max_distance), sense = maximize)
	return model

def add_cost_minimzation_objective(model):
	##### DEFINE OBJECTIVE
	model.obj_cost_minimzation = Objective(expr = sum(model.var_hub_yn[site]*model.param_site_cost[site] for site in model.idx_sites), sense = minimize)
	return model


def add_weighted_demand_maximization_objective(model,max_distance = 10000000):
	##### DEFINE OBJECTIVE
	model.max_coverage = Objective(expr = sum(model.param_bg_vuln_ces[pair[0]]*model.var_prop_bg_at_site[pair]*model.param_bg_pop[pair[0]] for pair in model.idx_bg_site_pairs if model.param_bg_site_dist[pair]<=max_distance), sense = maximize)
	return model

def constrain_total_cost(model,max_cost):
	model.max_cost = Constraint(expr = sum(model.var_hub_yn[site]*model.param_site_cost[site] for site in model.idx_sites)<=max_cost)
	return model

##### GET RESULTS FROM SAVED MODEL

def get_variables_from_model(model):
	hubs_df=pd.DataFrame([int(model.var_hub_yn[site].value) for site in model.idx_sites],columns = ["BUILT"],index=model.idx_sites)
	hubs_df["CAPACITY"] = [model.param_site_kw_cap[site] for site in hubs_df.index]
	bgs_df = pd.DataFrame([model.param_bg_pop[bg] for bg in model.idx_bgs],columns = ["POPULATION"], index=model.idx_bgs)
	prop_served_list = []
	distances_list = []
	for cg in model.idx_bgs:
		cg_dict = dict();
		dist_dict = dict()
		for pair in model.idx_bg_site_pairs:
			if pair[0]==cg:
				cg_dict[pair[1]] = model.var_prop_bg_at_site[pair].value;
				dist_dict[pair[1]] = model.param_bg_site_dist[pair]
		prop_served_list.append(cg_dict);
		distances_list.append(dist_dict)
	prop_served = pd.DataFrame(prop_served_list,index = model.idx_bgs);
	distance_matrix = pd.DataFrame(distances_list,index = model.idx_bgs)

	return hubs_df, bgs_df, prop_served, distance_matrix













"""
Following is code from Audrey, I don't use much of it at all.
"""

##### SOLVE MODEL AND SAVE RESULTS

### Get base path to save results
def make_result_path():

	result_folder = 'results/p-med/'
	result_time  = datetime.now().strftime('%Y-%m-%d_%H%M')
	result_path = result_folder + result_time

	return(result_path)

### Solve the model
def solve_model(model, result_path):

	result = pyopt.SolverFactory('gurobi').solve(model)

	result_path_file = result_path + '.mps'
	model.write(result_path_file)

	return(print(result))

### Save results - which sites are hubs?
def save_results_hubs(model, result_path):

	result_site = [site for site in model.idx_sites]
	result_hub_yn = [model.var_hub_yn[site].value for site in model.idx_sites]

	result_hub_yn_df = pd.DataFrame({'site_id': result_site, 'site_yn':result_hub_yn})

	result_hub_yn_df = result_hub_yn_df.loc[result_hub_yn_df['site_yn'] > 0]

	result_hub_yn_path_file = result_path + '_hub_yn.csv'
	result_hub_yn_df.to_csv(result_hub_yn_path_file)

	return(result_hub_yn_df.shape[0])

### Save results - what proportion of blockgroup assigned to given hub?
def save_results_prop_bg_at_site(model, result_path, dist_to_site_df):

	prop_bg_at_site_df = dist_to_site_df.copy()
	prop_bg_at_site_df.loc[:] = np.NaN

	for key in model.var_prop_bg_at_site.keys():
	    prop_bg_at_site_df.loc[key] = model.var_prop_bg_at_site[key].value

	result_prop_served_dict = {}

	for key in model.var_prop_bg_at_site.keys():
	    if prop_bg_at_site_df.loc[key]:
	        result_prop_served_dict[key] = model.var_prop_bg_at_site[key].value

	result_prop_served_hubs = set([key[1] for key in result_prop_served_dict.keys()])
	result_prop_served_bgs = set([key[0] for key in result_prop_served_dict.keys()])

	result_prop_served_df = pd.DataFrame(index = result_prop_served_bgs, columns = result_prop_served_hubs)

	for bg, hub in result_prop_served_dict.keys():
	    result_prop_served_df.loc[bg, hub] = result_prop_served_dict[bg, hub]

	result_prop_served_df.fillna(0, inplace = True)

	result_prop_served_path = result_path + '_prop_served.csv'
	result_prop_served_df.to_csv(result_prop_served_path)

	return(result_prop_served_df, result_prop_served_dict)

def save_results_dist_traveled(result_prop_served_df, result_prop_served_dict, result_path, dist_to_site_dict):

	result_dist_traveled_df = result_prop_served_df.copy()

	for bg, hub in result_prop_served_dict.keys():

	    result_dist_traveled_df.loc[bg, hub] = dist_to_site_dict[bg, hub]*result_prop_served_df.loc[bg, hub]*blockgroup_pop_dict[bg]

	result_dist_traveled_path = result_path + '_dist_traveled.csv'
	result_dist_traveled_df.to_csv(result_dist_traveled_path)

	return(result_dist_traveled_df.sum().sum())

def save_results_pop_served(result_prop_served_df, result_prop_served_dict, result_path, blockgroup_pop_dict):

	result_pop_df = result_prop_served_df.copy()

	for bg, hub in result_prop_served_dict.keys():

	    result_pop_df.loc[bg, hub] = result_prop_served_df.loc[bg, hub]*blockgroup_pop_dict[bg]

	result_pop_path = result_path + '_pop.csv'
	result_pop_df.to_csv(result_pop_path)

	return(result_pop_df.sum().sum())

def save_results_ces(result_prop_served_df, result_prop_served_dict, result_pop_served, result_path, bg_ces_dict, blockgroup_pop_dict):
	result_ces_df = result_prop_served_df.copy()

	for bg, hub in result_prop_served_dict.keys():

	    result_ces_df.loc[bg, hub] = bg_ces_dict[bg]*result_prop_served_df.loc[bg, hub]*blockgroup_pop_dict[bg]

	result_ces_path = result_path + '_ces.csv'

	result_ces_df.to_csv(result_ces_path)

	return(result_ces_df.sum().sum()/result_pop_served)
