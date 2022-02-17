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
                           hub_occ_dict):

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


    # Create variable -how many people are served at this hub?
    # model.var_popu_served = Var(model.hubs, initialize = 0.0, within = NonNegativeReals)

    # Objective - minimize population weighted travel distance to hubs
    # model.obj_min_agg_dist = Objective(expr = sum(model.cg_hub_distance[cg, hub] * cengeo_pop_dict[cg] * model.var_prop_served[cg, hub] for cg, hub in model.cg_hub_nearby_pairs), sense = minimize)

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

    # model.coverage_constraints = ConstraintList()
    # for cg in model.cengeos:
    #     if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1:
    #         model.coverage_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)>=min_fraction_covered)

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
