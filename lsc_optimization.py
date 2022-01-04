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

model.cengeos = np.unique([key[0] for key in dist_to_hub_dict.keys()])
model.hubs = np.unique([key[1] for key in dist_to_hub_dict.keys()])

model.var_hub_yn = Var(model.hubs, initialize = 0, within = Binary)
model.var_prop_served = Var(model.cengeos, model.hubs, initialize = 0.0, bounds = (0.0, 1.0))

model.objective = Objective(expr = sum(dist_to_hub_dict[cg_hub] * cengeo_pop_dict[cg_hub[0]] * model.var_prop_served[cg_hub] for cg_hub in dist_to_hub_dict.keys()), sense = minimize)

##########################################
###### DEFINE CONSTRAINTS
model.con_min_coverage = Constraint(expr = sum(cengeo_pop_dict[cg_hub[0]]*model.var_prop_served[cg_hub] for cg_hub in dist_to_hub_dict.keys()) >= 0.75*sum(cengeo_pop_dict[cg] for cg in model.cengeos))
model.con_max_hubs = Constraint(expr = sum(model.var_hub_yn[hub] for hub in model.hubs) == 5)




#model.constraints.add(expr = sum(model.var_prop_served * model.param_cengeo_pop) >= 0.75) #At least 75 of Richmond pop must be assigned to hub
#model.constraints.add(expr = sum(model.var_prop_served * model.param_cengeo_pop) <= model.param_hub_capacity) #Pop assigned to given hub cannot exceed hub capacity
#model.constraints.add(expr = model.param_dist_to_hub <= 1.5) #Drive distance from centroid to hub cannot exceed 1.5 miles



































###
