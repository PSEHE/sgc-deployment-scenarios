# %% markdown
# set_min indicates that this is doing a set minimization by maximizing the population served.
# min_block indicates that a certain minimum population from each blockgroup must be served.

# %% markdown


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
from data_cleaning import bg_ces_df

dist_to_hub_df = pd.read_csv('data/distmatrix_bbox.csv')
dist_to_hub_df.set_index("Unnamed: 0",inplace = True)

dist_to_hub_df[dist_to_hub_df>2] = np.NaN
# blah = dist_to_hub_df.copy()
blah1 = dist_to_hub_df.notnull().sum(axis=0)==0
dist_to_hub_df.drop(columns = blah1[blah1].index,inplace=True)
blah2 = dist_to_hub_df.notnull().sum(axis=1)==0
dist_to_hub_df.drop(index = blah2[blah2].index,inplace=True)
 # dist_to_hub_df.notnull().sum(axis=0)==0
# %%markdown
# # User model parameters
# %%markdown
# %% codecell
max_hubs = 50
min_fraction_covered = 0.05
# %% codecell


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
# model.var_prop_served = Var(model.cg_hub_nearby_pairs, initialize = 0.0, bounds = (0.0, 1.0))
model.var_prop_served = Var(model.cg_hub_nearby_pairs, bounds = (0.0, 1.0))


# Create variable -how many people are served at this hub?
# model.var_popu_served = Var(model.hubs, initialize = 0.0, within = NonNegativeReals)

# Objective - minimize population weighted travel distance to hubs
# model.obj_min_agg_dist = Objective(expr = sum(model.cg_hub_distance[cg, hub] * cengeo_pop_dict[cg] * model.var_prop_served[cg, hub] for cg, hub in model.cg_hub_nearby_pairs), sense = minimize)
def objective_max_coverage(model,pairs):
    coverage = 0
    for pair in pairs:
        if model.var_hub_yn[pair[1]]:
            coverage+=model.model.var_prop_served[pair]*cengeo_pop_dict[pair[1]]
    return coverage
model.max_coverage = Objective(expr = sum(sum(cengeo_pop_dict[cg] * model.var_prop_served[cg, hub] for cg, hub in model.cg_hub_nearby_pairs if c), sense = minimize)


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
# def open_only(model, cg, hub):
#     return model.var_prop_served[cg, hub] <= model.var_hub_yn[hub]

model.con_open_only = Constraint(model.cg_hub_nearby_pairs, rule = open_only)

# At least some percent Richmond population must be assigned a hub
model.con_min_coverage = Constraint(expr = sum(model.var_popu_served[hub] for hub in model.hubs) >= 0.5*sum(cengeo_pop_dict[cg] for cg in model.cengeos))

#
model.coverage_constraints = ConstraintList()
for cg in model.cengeos:
    if sum([pair[0]==cg for pair in model.cg_hub_nearby_pairs]) >= 1:
        model.coverage_constraints.add(expr = sum(model.var_prop_served[pair] for pair in model.cg_hub_nearby_pairs if pair[0]==cg)>=min_fraction_covered)

# %% codecell
# People assigned to hub cannot exceed 5x hub capacity - to be refined
model.capacity_constraints = ConstraintList()
for hub in model.hubs:
    # Only add constraint for hubs that have a nearby blockgroup, returns error if "if" statement ommited
    if sum([pair[1]==hub for pair in model.cg_hub_nearby_pairs]) >= 1:
        model.capacity_constraints.add(expr = sum(model.var_prop_served[cg,h_pair]*cengeo_pop_dict[cg] for cg,h_pair in model.cg_hub_nearby_pairs if h_pair==hub)<=model.param_max_occ[hub])
    # model.capacity_constraints.add(expr = sum(model.var_prop_served[pair]*cengeo_pop_dict[pair[0]]*tmp_dict[pair] for pair in model.cg_hub_nearby_pairs)<=model.param_max_occ[hub])
    # model.capacity_constraints.add(expr = expr<=model.param_max_occ[hub]+0)
    # pairs = [pair for pair in model.cg_hub_nearby_pairs if pair[1]==hub]
    # model.capacity_constraint.add(sum(model.var_prop_served[pairs]*cengeo_pop_dict[cg])<=model.param_max_occ[hub])
# model.var_prop_served[0].pprint()
# ALl demand must be met in the hottest block blockgroups
#cg_area = []

#for pair in model.cg_hub_nearby_pairs:
    #if pair[0] not in cg_area:
        #cg_area.append(pair[0])

#cg_hottest = heatdays_df.loc[heatdays_df['GISJOIN'].isin(cg_area)][0:10]['GISJOIN']

#def filter_to_hot_cgs(model, cg, hub):
    #return(model.var_prop_served[(cg, hub)] for cg in cg_area)

#model.con_prioritize_hot = Constraint(expr = sum(cengeo_pop_dict[cg]*model.var_prop_served[(cg, hub)] for cg, hub in model.cg_hub_nearby_pairs) >= 0.999*sum(cengeo_pop_dict[cg] for cg, hub in model.cg_hub_nearby_pairs))

# %% codecell
5
# Run model and extract and save results

from pyomo.opt import SolverFactory
SolverFactory('glpk').solve(model)
var_popu_served = [model.var_popu_served[hub].value for hub in model.hubs]
var_hub_yn = [model.var_hub_yn[hub].value for hub in model.hubs]
prop_served_list = []
for cg in model.cengeos:
    cg_dict = dict()
    for pair in model.cg_hub_nearby_pairs:
        if pair[0]==cg:
            cg_dict[pair[1]] = model.var_prop_served[pair].value
    prop_served_list.append(cg_dict)
var_prop_served = pd.DataFrame(prop_served_list)

np.unique(var_popu_served)
np.unique(var_prop_served)
np.unique(var_hub_yn)

###
