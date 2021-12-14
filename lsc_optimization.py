##########################################
# %% codecell
import pandas as pd
import pyomo.environ as pe
import pyomo.opt as po

from distance_matrix_calculation import dist_to_hub_df

##########################################
# %% codecell
### Set up vars
cengeos = [cengeo for cengeo in dist_to_hub_df.index]
hubs = [hub for hub in dist_to_hub_df.columns]

dist_to_hub_df.loc[cengeos[0]][hubs[0]]
#travel_dist =
travel_max = 1.5
hubs_max = 5

##########################################
# %% codecell
### Define model
model = pe.ConcreteModel()

model.cengeos = Set(initialize=cengeos)
model.hubs = Set(initialize=hubs)
model.travel_max = travel_max

##########################################
# %% codecell


from pyomo.environ import *
import random

number_of_hubs = 10000

random.seed(1000)

model.distances = Param(model.blockgroups,model.hubs,distance_matrix)
model.ishub = Var(model.hubs,within=Binary)
# model.capacity_hub = Var(model.hubs,within=PositiveIntegers)

def max_number_hubs(model, number_of_hubs):
    return sum(model.ishub[hub] for hub in model.hubs) <= number_of_hubs
model.demand = Constraint(model.N, rule=max_number_hubs)

def cost_(model):
    return somefunction for hub in model.hub for cengeo in model.blockgroups)
model.cost = Objective(rule=cost_, sense="Minimize")
