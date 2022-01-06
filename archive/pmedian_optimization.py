# %% markdown

# 1) Load in the distance matrix
# 2) Start a ConcreteModel()
# 3) enter list of parameters
# PARAMETERS: PositiveIntegers

# %%codecell

from pyomo.environ import *
import random

from distance_matrix_calculation import dist_to_hub_df

number_of_hubs = 10000

random.seed(1000)

model = ConcreteModel()
model.blockgroups = Set(GISJOINS)
model.hubs = Set(hub_IDs)

model.distances = Param(model.blockgroups,model.hubs,distance_matrix)
model.ishub = Var(model.hubs,within=Binary)
# model.capacity_hub = Var(model.hubs,within=PositiveIntegers)

def max_number_hubs(model, number_of_hubs):
    return sum(model.ishub[hub] for hub in model.hubs) <= number_of_hubs
model.demand = Constraint(model.N, rule=max_number_hubs)

def cost_(model):
    return somefunction for hub in model.hub for cengeo in model.blockgroups)
model.cost = Objective(rule=cost_, sense="Minimize")

# answer = model.solve()
