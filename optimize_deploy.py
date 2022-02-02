##########################################
###### IMPORT PACKAGES AND DATA
# %% codecell
import pandas as pd
import numpy as np

from pyomo.environ import *

from data_cleaning import hub_occ_dict
from data_cleaning import hub_sqft_dict
from data_cleaning import heatdays_df
from data_cleaning import cengeo_pop_dict

dist_to_hub_df = pd.read_csv('data/distmatrix_contracosta.csv')

##########################################
###### DEFINE MODEL
# %%codecell
# Define concrete model
model = ConcreteModel()

# Attach census geographies and hubs to model
model.cengeos = Set(initialize = dist_to_hub_df.index)
model.hubs = Set(initialize = dist_to_hub_df.columns)

# Get hub square footages
model.hub_sqft_dict = hub_sqft_dict

# Get distance between hubs
model.dist_to_hub_df = dist_to_hub_df

def filter_to_nearby_hubs(model, cg, hub):
    return not(np.isnan(model.dist_to_hub_df.loc[cg, hub]))

model.cg_hub_nearby_pairs = Set(initialize = model.cengeos*model.hubs, filter = filter_to_nearby_hubs)

def get_cg_hub_distance(model, cg, hub):
    return model.dist_to_hub_df.loc[cg, hub]

model.cg_hub_distance = Param(model.cg_hub_nearby_pairs, initialize = get_cg_hub_distance)

# Create variable - is this site a hub?
model.var_hub_yn = Var(model.hubs, initialize = 0, within = Binary)

# Create variable - what percent of a census geography's population is served by this hub?
model.var_prop_served = Var(model.cg_hub_nearby_pairs, initialize = 0.0, bounds = (0.0, 1.0))

# Create variable -how many people are served at this hub?
model.var_popu_served = Var(model.hubs, initialize = 0.0, within = NonNegativeReals)

# Objective - minimize population weighted travel distance to hubs
model.obj_min_agg_dist = Objective(expr = sum(model.cg_hub_distance[cg, hub] * cengeo_pop_dict[cg] * model.var_prop_served[cg, hub] for cg, hub in model.cg_hub_nearby_pairs), sense = minimize)

##########################################
###### DEFINE PARAMETERS
# Max quantity of people served at hub dependent on max capacity
hub_capacity_dict = {hub : hub_occ_dict[hub] for hub in model.hubs}
model.param_max_occ = Param(model.hubs, initialize = hub_capacity_dict)

##########################################
###### DEFINE CONSTRAINTS
# Construct no more than a set number of hubs
model.con_max_hubs = Constraint(expr = sum(model.var_hub_yn[hub] for hub in model.hubs) == 3)

# No one is served at location if it is not a hub
def open_only(model, cg, hub):
    return model.var_prop_served[cg, hub] <= model.var_hub_yn[hub]

model.con_open_only = Constraint(model.cg_hub_nearby_pairs, rule = open_only)

# At least some percent Richmond population must be assigned a hub
model.con_min_coverage = Constraint(expr = sum(model.var_popu_served[hub] for hub in model.hubs) >= 0.5*sum(cengeo_pop_dict[cg] for cg in model.cengeos))

# People assigned to hub cannot exceed 5x hub capacity - to be refined
def serve_less_than_occ(model, hub):
    tot_pop_served = 0

    for cg in model.cengeos:
        if (cg, hub) in model.cg_hub_nearby_pairs:
            pop_served = model.var_prop_served[cg, hub]*cengeo_pop_dict[cg]
            tot_pop_served = pop_served + tot_pop_served
    model.var_popu_served[hub] = tot_pop_served

    return model.var_popu_served[hub] <= model.param_max_occ[hub]

model.con_max_occ = Constraint(model.hubs, rule = serve_less_than_occ)

# ALl demand must be met in the hottest block blockgroups
#cg_area = []

#for pair in model.cg_hub_nearby_pairs:
    #if pair[0] not in cg_area:
        #cg_area.append(pair[0])

#cg_hottest = heatdays_df.loc[heatdays_df['GISJOIN'].isin(cg_area)][0:10]['GISJOIN']

#def filter_to_hot_cgs(model, cg, hub):
    #return(model.var_prop_served[(cg, hub)] for cg in cg_area)

#model.con_prioritize_hot = Constraint(expr = sum(cengeo_pop_dict[cg]*model.var_prop_served[(cg, hub)] for cg, hub in model.cg_hub_nearby_pairs) >= 0.999*sum(cengeo_pop_dict[cg] for cg, hub in model.cg_hub_nearby_pairs))













###
