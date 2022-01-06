##########################################
###### IMPORT PACKAGES AND DATA
# %% codecell
import pandas as pd
import numpy as np

from pyomo.environ import *

from data_cleaning import hub_occ_dict
from data_cleaning import dist_to_hub_df
from data_cleaning import dist_to_hub_dict
from data_cleaning import cengeo_pop_dict

##########################################
###### DEFINE MODEL
# %%codecell
# Define concrete model
model = ConcreteModel()

# Attach census geographies and hubs to model
model.cengeos = Set(initialize = dist_to_hub_df.index)
model.hubs = Set(initialize = dist_to_hub_df.columns)

# Create variable - is this site a hub?
model.var_hub_yn = Var(model.hubs, initialize = 0, within = Binary)

# Create variable - what percent of a census geography's population is served by this hub?
model.var_prop_served = Var(model.cengeos, model.hubs, initialize = 0.0, bounds = (0.0, 1.0))

# Objective - minimize population weighted travel distance to hubs
model.objective = Objective(expr = sum(dist_to_hub_df.loc[cg, hub] * cengeo_pop_dict[cg] * model.var_prop_served[cg, hub] for hub in model.hubs for cg in model.cengeos), sense = minimize)

##########################################
###### DEFINE CONSTRAINTS
# At least some percent Richmond population must be assigned a hub
model.con_min_coverage = Constraint(expr = sum(cengeo_pop_dict[cg]*model.var_prop_served[cg, hub] for hub in model.hubs for cg in model.cengeos) >= 0.98*sum(cengeo_pop_dict[cg] for cg in model.cengeos))

# No one is served at hub if it is not a hub
def open_only(model, cg, hub):
    return model.var_prop_served[cg, hub] <= model.var_hub_yn[hub]

model.con_open_only = Constraint(model.cengeos, model.hubs, rule=open_only)

# Construct a set number of hubs
model.con_max_hubs = Constraint(expr = sum(model.var_hub_yn[hub] for hub in model.hubs) <= 1)

# People assigned to hub cannot exceed 5x hub capacity
model.con_hub_capacity = ConstraintList()

for hub in model.hubs:
    max_capacity = 5*hub_occ_dict[hub]
    model.con_hub_capacity.add(max_capacity >= sum(model.var_prop_served[cg, hub]*cengeo_pop_dict[cg] for cg in model.cengeos))





































###
