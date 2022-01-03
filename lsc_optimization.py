##########################################
###### IMPORT PACKAGES AND DATA
# %% codecell
import pandas as pd
import numpy as np

from pyomo.environ import *

from data_cleaning import hub_occ_dict
from data_cleaning import dist_to_hub_dict
from data_cleaning import cengeo_pop_dict

##########################################
###### DEFINE MODEL
# %%codecell
model = ConcreteModel()

model.set_cengeos = Set(initialize = np.unique([key[0] for key in dist_to_hub_dict.keys()]))
model.set_hubs = Set(initialize = np.unique([key[1] for key in dist_to_hub_dict.keys()]))

model.data_dist_to_hubs = dist_to_hub_dict
model.data_hub_capacity = hub_occ_dict
model.data_cengeo_pop = cengeo_pop_dict

model.var_hub_yn = Var(model.set_hubs, within = Binary)
model.var_prop_served = Var(model.set_cengeos, model.set_hubs, bounds = (0.0, 1.0))

model.obj_min_dist = Objective(expr = sum(dist_to_hub_dict[key[0], key[1]] * cengeo_pop_dict[key[0]] * model.var_prop_served[key[0], key[1]] * model.var_hub_yn[key[1]] for key in dist_to_hub_dict))

##########################################
###### DEFINE CONSTRAINTS
model.constraints = ConstraintList()

model.constraints.add(expr = sum(model.var_cengeo_prop_served * model.param_cengeo_pop) >= 0.75) #At least 75 of Richmond pop must be assigned to hub
model.constraints.add(expr = sum(model.var_cengeo_prop_served * model.param_cengeo_pop) <= model.param_hub_capacity) #Pop assigned to given hub cannot exceed hub capacity
model.constraints.add(expr = model.param_dist_to_hub <= 1.5) #Drive distance from centroid to hub cannot exceed 1.5 miles






































###
