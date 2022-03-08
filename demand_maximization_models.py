import pandas as pd
import numpy as np
from pyomo.environ import *
import os
import pyomo
from pyomo.opt import SolverFactory
import time

##########################################
###### DEFINE MODEL
# %%codecell
# Define concrete model

def build_demand_max_model(max_hubs,
                           max_distance,
                           dist_to_hub_df,
                           hub_sqft_dict,
                           cengeo_pop_dict,
                           hub_occ_dict,
                           bg_ces_df,
                           min_fraction_covered = 0.05):

    model = ConcreteModel()

    # Attach census geographies and hubs to model
    model.cengeos = Set(initialize = dist_to_hub_df.index)
    model.hubs = Set(initialize = dist_to_hub_df.columns)

    # Get hub square footages
    model.hub_sqft_dict = hub_sqft_dict

    # Get distance between hubs
    model.dist_to_hub_df = dist_to_hub_df.copy()
    model.dist_to_hub_df[model.dist_to_hub_df>max_distance] = np.NaN

    def filter_to_nearby_hubs(model, cg, hub):
        return not(np.isnan(model.dist_to_hub_df.loc[cg, hub]))

    model.cg_hub_nearby_pairs = Set(initialize = model.cengeos*model.hubs, filter = filter_to_nearby_hubs)

    def get_cg_hub_distance(model, cg, hub):
        return model.dist_to_hub_df.loc[cg, hub]

    model.cg_hub_distance = Param(model.cg_hub_nearby_pairs, initialize = get_cg_hub_distance)

    # Create variable - is this site a hub?
    model.var_hub_yn = Var(model.hubs, initialize = 0, within = Binary)

    # Create variable - what percent of a census geography's population is served by this hub?
    # model.var_prop_served = Var(model.cg_hub_nearby_pairs, initialize = 0.0, bounds = (0.0, 1.0))
    model.var_prop_served = Var(model.cg_hub_nearby_pairs, bounds = (0.0, 1.0))

    ##########################################
    ###### DEFINE PARAMETERS
    # Max quantity of people served at hub dependent on max capacity
    hub_capacity_dict = {hub : hub_occ_dict[hub] for hub in model.hubs}
    model.param_max_occ = Param(model.hubs, initialize = hub_capacity_dict)

    ##########################################
    ###### DEFINE CONSTRAINTS
    # Construct no more than a set number of hubs
    model.con_max_hubs = Constraint(expr = sum(model.var_hub_yn[hub] for hub in model.hubs) <= max_hubs)

    # No one is served at location if it is not a hub
    def open_only(model, cg, hub):
        return model.var_prop_served[cg, hub] <= model.var_hub_yn[hub]
    model.con_open_only = Constraint(model.cg_hub_nearby_pairs, rule = open_only)

    model.coverage_constraints = ConstraintList()
    for cg in model.cengeos:
        if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1: # If a blockgroup has at least one hub
            model.coverage_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)>=min_fraction_covered)

    # %% codecell
    model.capacity_constraints = ConstraintList()
    for hub in model.hubs:
        # Only add constraint for hubs that have a nearby blockgroup, returns error if "if" statement ommited
        if sum([pair[1]==hub for pair in model.cg_hub_nearby_pairs]) >= 1:
            model.capacity_constraints.add(expr = sum(model.var_prop_served[cg,h_pair]*cengeo_pop_dict[cg] for cg,h_pair in model.cg_hub_nearby_pairs if h_pair==hub)<=model.param_max_occ[hub])

    model.demand_constraints = ConstraintList() #Constrain the TOTAL proportion of people assigned a hub to be 100 percent
    for cg in model.cengeos:
        # Only add constraint for cengeos that have hubs, may return error if "if" statement ommited
        if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1:
            model.demand_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)<=1)


    # def objective_max_coverage(model):
    #     coverage = 0
    #     for pair in model.pairs:
    #         coverage+=model.var_hub_yn[pair[1]]*model.model.var_prop_served[pair]*cengeo_pop_dict[pair[1]]
    #     return coverage
    model.max_coverage = Objective(expr = sum(model.var_prop_served[pair]*cengeo_pop_dict[pair[0]] for pair in model.cg_hub_nearby_pairs), sense = maximize)

    # %% codecell
    # Run model and extract and save results
    tic = time.perf_counter()
    SolverFactory('gurobi').solve(model)
    toc = time.perf_counter()
    elapsed = toc-tic
    print("Time to solve model: ", elapsed)

    # var_popu_served = [model.var_popu_served[hub].value for hub in model.hubs]
    var_hub_yn = [model.var_hub_yn[hub].value for hub in model.hubs]
    var_hub_yn=pd.DataFrame(var_hub_yn,index=model.hubs)

    prop_served_list = []
    for cg in model.cengeos:
        cg_dict = dict()
        for pair in model.cg_hub_nearby_pairs:
            if pair[0]==cg:
                cg_dict[pair[1]] = model.var_prop_served[pair].value
        prop_served_list.append(cg_dict)
    var_prop_served = pd.DataFrame(prop_served_list,index = model.cengeos)

    # var_prop_served.to_csv(os.path.join("results",run_string+"var_prop_served.csv"))
    # var_hub_yn.to_csv(os.path.join("results",run_string+"var_hub_yn.csv"))
    return var_prop_served, var_hub_yn

def build_demand_max_ces_model(max_hubs,
                           max_distance,
                           dist_to_hub_df,
                           hub_sqft_dict,
                           cengeo_pop_dict,
                           hub_occ_dict,
                           bg_ces_df,
                           ces_multiplier = 1.0):
    """
    ces_multiplier is a number from 0 to 1. Minimum demand from blockgroups must be met is
    ces_multiplier * CalEnviroScree score. For example, if a blockgroup has a score of 50 percent
    and the ces_multiplier is 0.5, then at least 25 percent of the demand from that blockgroup must be met.
    """

    model = ConcreteModel()

    # Attach census geographies and hubs to model
    model.cengeos = Set(initialize = dist_to_hub_df.index)
    model.hubs = Set(initialize = dist_to_hub_df.columns)

    # Get hub square footages
    model.hub_sqft_dict = hub_sqft_dict

    # Get distance between hubs
    model.dist_to_hub_df = dist_to_hub_df.copy()
    model.dist_to_hub_df[model.dist_to_hub_df>max_distance] = np.NaN

    def filter_to_nearby_hubs(model, cg, hub):
        return not(np.isnan(model.dist_to_hub_df.loc[cg, hub]))

    model.cg_hub_nearby_pairs = Set(initialize = model.cengeos*model.hubs, filter = filter_to_nearby_hubs)

    def get_cg_hub_distance(model, cg, hub):
        return model.dist_to_hub_df.loc[cg, hub]

    model.cg_hub_distance = Param(model.cg_hub_nearby_pairs, initialize = get_cg_hub_distance)

    # Create variable - is this site a hub?
    model.var_hub_yn = Var(model.hubs, initialize = 0, within = Binary)

    # Create variable - what percent of a census geography's population is served by this hub?
    # model.var_prop_served = Var(model.cg_hub_nearby_pairs, initialize = 0.0, bounds = (0.0, 1.0))
    model.var_prop_served = Var(model.cg_hub_nearby_pairs, bounds = (0.0, 1.0))

    ##########################################
    ###### DEFINE PARAMETERS
    # Max quantity of people served at hub dependent on max capacity
    hub_capacity_dict = {hub : hub_occ_dict[hub] for hub in model.hubs}
    model.param_max_occ = Param(model.hubs, initialize = hub_capacity_dict)

    ##########################################
    ###### DEFINE CONSTRAINTS
    # Construct no more than a set number of hubs
    model.con_max_hubs = Constraint(expr = sum(model.var_hub_yn[hub] for hub in model.hubs) <= max_hubs)

    # No one is served at location if it is not a hub
    def open_only(model, cg, hub):
        return model.var_prop_served[cg, hub] <= model.var_hub_yn[hub]
    model.con_open_only = Constraint(model.cg_hub_nearby_pairs, rule = open_only)

    model.coverage_constraints = ConstraintList()
    for cg in model.cengeos:
        if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1: # If a blockgroup has at least one hub
            model.coverage_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)>=ces_multiplier*bg_ces_df.loc[cg,"SCORE_PCTL_CI_BG"]/100)

    # %% codecell
    model.capacity_constraints = ConstraintList()
    for hub in model.hubs:
        # Only add constraint for hubs that have a nearby blockgroup, returns error if "if" statement ommited
        if sum([pair[1]==hub for pair in model.cg_hub_nearby_pairs]) >= 1:
            model.capacity_constraints.add(expr = sum(model.var_prop_served[cg,h_pair]*cengeo_pop_dict[cg] for cg,h_pair in model.cg_hub_nearby_pairs if h_pair==hub)<=model.param_max_occ[hub])

    model.demand_constraints = ConstraintList() #Constrain the TOTAL proportion of people assigned a hub to be 100 percent
    for cg in model.cengeos:
        # Only add constraint for cengeos that have hubs, may return error if "if" statement ommited
        if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1:
            model.demand_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)<=1)


    # def objective_max_coverage(model):
    #     coverage = 0
    #     for pair in model.pairs:
    #         coverage+=model.var_hub_yn[pair[1]]*model.model.var_prop_served[pair]*cengeo_pop_dict[pair[1]]
    #     return coverage
    model.max_coverage = Objective(expr = sum(model.var_prop_served[pair]*cengeo_pop_dict[pair[0]] for pair in model.cg_hub_nearby_pairs), sense = maximize)

    # %% codecell
    # Run model and extract and save results
    tic = time.perf_counter()
    SolverFactory('gurobi').solve(model)
    toc = time.perf_counter()
    elapsed = toc-tic
    print("Time to solve model: ", elapsed)

    # var_popu_served = [model.var_popu_served[hub].value for hub in model.hubs]
    var_hub_yn = [model.var_hub_yn[hub].value for hub in model.hubs]
    var_hub_yn=pd.DataFrame(var_hub_yn,index=model.hubs)

    prop_served_list = []
    for cg in model.cengeos:
        cg_dict = dict()
        for pair in model.cg_hub_nearby_pairs:
            if pair[0]==cg:
                cg_dict[pair[1]] = model.var_prop_served[pair].value
        prop_served_list.append(cg_dict)
    var_prop_served = pd.DataFrame(prop_served_list,index = model.cengeos)

    # var_prop_served.to_csv(os.path.join("results",run_string+"var_prop_served.csv"))
    # var_hub_yn.to_csv(os.path.join("results",run_string+"var_hub_yn.csv"))
    return var_prop_served, var_hub_yn


def build_demand_max_ces_cost_model(max_cost,
                           max_distance,
                           dist_to_hub_df,
                           hub_sqft_dict,
                           cengeo_pop_dict,
                           hub_occ_dict,
                           bg_ces_df,
                           ces_multiplier = 1.0,
                           cost_per_hub = 100,
                           cost_per_capita = 1):
    """
    ces_multiplier is a number from 0 to 1. Minimum demand from blockgroups must be met is
    ces_multiplier * CalEnviroScree score. For example, if a blockgroup has a score of 50 percent
    and the ces_multiplier is 0.5, then at least 25 percent of the demand from that blockgroup must be met.
    """

    model = ConcreteModel()

    # Attach census geographies and hubs to model
    model.cengeos = Set(initialize = dist_to_hub_df.index)
    model.hubs = Set(initialize = dist_to_hub_df.columns)

    # Get hub square footages
    model.hub_sqft_dict = hub_sqft_dict

    # Get distance between hubs
    model.dist_to_hub_df = dist_to_hub_df.copy()
    model.dist_to_hub_df[model.dist_to_hub_df>max_distance] = np.NaN

    def filter_to_nearby_hubs(model, cg, hub):
        return not(np.isnan(model.dist_to_hub_df.loc[cg, hub]))

    model.cg_hub_nearby_pairs = Set(initialize = model.cengeos*model.hubs, filter = filter_to_nearby_hubs)

    def get_cg_hub_distance(model, cg, hub):
        return model.dist_to_hub_df.loc[cg, hub]

    model.cg_hub_distance = Param(model.cg_hub_nearby_pairs, initialize = get_cg_hub_distance)

    # Create variable - is this site a hub?
    model.var_hub_yn = Var(model.hubs, initialize = 0, within = Binary)

    # Create variable - what percent of a census geography's population is served by this hub?
    # model.var_prop_served = Var(model.cg_hub_nearby_pairs, initialize = 0.0, bounds = (0.0, 1.0))
    model.var_prop_served = Var(model.cg_hub_nearby_pairs, bounds = (0.0, 1.0))

    ##########################################
    ###### DEFINE PARAMETERS
    # Max quantity of people served at hub dependent on max capacity
    hub_capacity_dict = {hub : hub_occ_dict[hub] for hub in model.hubs}
    model.param_max_occ = Param(model.hubs, initialize = hub_capacity_dict)

    ##########################################
    ###### DEFINE CONSTRAINTS
    # # Construct no more than a set number of hubs
    # model.con_max_hubs = Constraint(expr = sum(model.var_hub_yn[hub] for hub in model.hubs) <= max_hubs)

    # Spend less than the money
    # model.cost_per_hub = cost_per_hub
    # model.max_cost = max_cost
    # model.cengeo_pop_dict = cengeo_pop_dict
    # def max_cost_function(model, cg, hub):
    #     hub_start_cost = sum(model.var_hub_yn[hub]*model.cost_per_hub for hub in model.hubs)
    #     hub_capita_cost = sum(model.var_prop_served[pair]*model.cengeo_pop_dict[pair[0]] for pair in model.cg_hub_nearby_pairs)
    #     return hub_start_cost+hub_capita_cost <= model.max_cost
    # model.con_max_cost = Constraint(rule = max_cost_function)
    #
    model.con_cost = Constraint(expr = cost_per_hub*sum(model.var_hub_yn[hub]*cost_per_hub for hub in model.hubs) +
                                cost_per_capita*sum(model.var_prop_served[pair]*cengeo_pop_dict[pair[0]] for pair in model.cg_hub_nearby_pairs) <= max_cost)

    # No one is served at location if it is not a hub
    def open_only(model, cg, hub):
        return model.var_prop_served[cg, hub] <= model.var_hub_yn[hub]
    model.con_open_only = Constraint(model.cg_hub_nearby_pairs, rule = open_only)

    model.coverage_constraints = ConstraintList()
    for cg in model.cengeos:
        if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1: # If a blockgroup has at least one hub
            model.coverage_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)>=ces_multiplier*bg_ces_df.loc[cg,"SCORE_PCTL_CI_BG"]/100)

    # %% codecell
    model.capacity_constraints = ConstraintList()
    for hub in model.hubs:
        # Only add constraint for hubs that have a nearby blockgroup, returns error if "if" statement ommited
        if sum([pair[1]==hub for pair in model.cg_hub_nearby_pairs]) >= 1:
            model.capacity_constraints.add(expr = sum(model.var_prop_served[cg,h_pair]*cengeo_pop_dict[cg] for cg,h_pair in model.cg_hub_nearby_pairs if h_pair==hub)<=model.param_max_occ[hub])

    model.demand_constraints = ConstraintList() #Constrain the TOTAL proportion of people assigned a hub to be 100 percent
    for cg in model.cengeos:
        # Only add constraint for cengeos that have hubs, may return error if "if" statement ommited
        if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1:
            model.demand_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)<=1)


    # def objective_max_coverage(model):
    #     coverage = 0
    #     for pair in model.pairs:
    #         coverage+=model.var_hub_yn[pair[1]]*model.model.var_prop_served[pair]*cengeo_pop_dict[pair[1]]
    #     return coverage
    model.max_coverage = Objective(expr = sum(model.var_prop_served[pair]*cengeo_pop_dict[pair[0]] for pair in model.cg_hub_nearby_pairs), sense = maximize)

    # %% codecell
    # Run model and extract and save results
    tic = time.perf_counter()
    SolverFactory('gurobi').solve(model)
    toc = time.perf_counter()
    elapsed = toc-tic
    print("Time to solve model: ", elapsed)

    # var_popu_served = [model.var_popu_served[hub].value for hub in model.hubs]
    var_hub_yn = [model.var_hub_yn[hub].value for hub in model.hubs]
    var_hub_yn=pd.DataFrame(var_hub_yn,index=model.hubs)

    prop_served_list = []
    for cg in model.cengeos:
        cg_dict = dict()
        for pair in model.cg_hub_nearby_pairs:
            if pair[0]==cg:
                cg_dict[pair[1]] = model.var_prop_served[pair].value
        prop_served_list.append(cg_dict)
    var_prop_served = pd.DataFrame(prop_served_list,index = model.cengeos)

    # var_prop_served.to_csv(os.path.join("results",run_string+"var_prop_served.csv"))
    # var_hub_yn.to_csv(os.path.join("results",run_string+"var_hub_yn.csv"))
    return var_prop_served, var_hub_yn
