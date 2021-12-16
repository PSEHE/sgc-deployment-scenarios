##########################################
# %% markdown
# Audrey: Get a list of capacities, input is as parameter
# Audrey: Input blockgroup popluations as a parameter
# Audrey: Code constraint parameter
# Yunus: Define a fraction variable (x_ij)
# Yunus: Handle the NaN issue
#
# model.blockgroups
# model.hubs
# model.capacities (length of hubs)
# model.fraction_pop (length of hubs times length of blockgroups)
# model.ishub (logical that is length of hubs)
# model.total_hubs (integer constant)
# model.population (length of blockgroups)
##########################################
# %% codecell
import pandas as pd
import numpy as np
from distance_matrix_calculation import dist_to_hub_df
from pyomo.environ import *
number_of_hubs = 10

model = ConcreteModel()
model.blockgroups = Set(initialize = dist_to_hub_df.index)
model.hubs = Set(initialize = dist_to_hub_df.columns)
model.dist_to_hub_df = dist_to_hub_df

def nan_filter(model,blockgroup,hub):
    return not(np.isnan(model.dist_to_hub_df.loc[blockgroup,hub]))
model.nearby_blockgroups_hubs = Set(initialize=model.blockgroups*model.hubs,filter=nan_filter)
def set_distance(model,blockgroup,hub):
    return model.dist_to_hub_df.loc[blockgroup,hub]
model.distances = Param(model.nearby_blockgroups_hubs,
                        initialize = set_distance)
model.distances.pprint()
model.ishub = Var(model.hubs,within=Binary)
