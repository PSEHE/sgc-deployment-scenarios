##########################################
# %% markdown
# Audrey: Get a list of capacities, input is as parameter
# Audrey: Input blockgroup popluations as a parameter
# Audrey: Code constraint parameter
#
# model.blockgroups
# model.hubs
# model.capacities (length of hubs)
# model.fraction_pop (length of hubs times length of blockgroups)
# model.ishub (logical that is length of hubs)
# model.total_hubs (integer constant)
# model.population (length of blockgroups)
##########################################
###### IMPORT PACKAGES AND DATA
# %% codecell
import pandas as pd
import numpy as np

from pyomo.environ import *

from data_cleaning import hub_occ_df
from data_cleaning import dist_to_hub_dict

cengeo_pop_df = pd.read_csv('data/bg_ca_19/blockgroup_pop_CA_19.csv')

##########################################
###### DEFINE MODEL
# %%codecell
model = ConcreteModel()

model.set_cengeos = Set(initialize = np.unique([key[0] for key in dist_to_hub_dict.keys()]))
model.set_hubs = Set(initialize = np.unique([key[1] for key in dist_to_hub_dict.keys()]))

model.var_hub_yn = Var(model.set_hubs, within = Binary)
model.var_prop_served = Var(model.set_cengeos, model.set_hubs, bounds = (0.0, 1.0))

model.obj_min_dist = Objective(expr = sum(dist_to_hub_dict[key[0], key[1]] * model.var_prop_served[key[0], key[1]] * model.var_hub_yn[key[1]] for key in dist_to_hub_dict))

##########################################
###### DEFINE PARAMETERS
model.param_dist_to_hub = Param()

model.param_hub_capacity = Param()

model.param_cengeo_pop = Param()

##########################################
###### DEFINE VARIABLES


##########################################
###### DEFINE OBJECTIVE

model.wt_dist_tot = Objective(expr = sum(model.var_cengeo_prop_served * model.param_cengeo_pop * model.param_dist_to_hub), sense = minimize)

##########################################
###### DEFINE CONSTRAINTS
model.constraints = ConstraintList()

model.constraints.add(expr = sum(model.var_cengeo_prop_served * model.param_cengeo_pop) >= 0.75) #At least 75 of Richmond pop must be assigned to hub
model.constraints.add(expr = sum(model.var_cengeo_prop_served * model.param_cengeo_pop) <= model.param_hub_capacity) #Pop assigned to given hub cannot exceed hub capacity
model.constraints.add(expr = model.param_dist_to_hub <= 1.5) #Drive distance from centroid to hub cannot exceed 1.5 miles






































###
