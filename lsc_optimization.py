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
###### IMPORT PACKAGES AND DATA
# %% codecell
import pandas as pd
from pyomo.environ import *

from distance_matrix_calculation import dist_to_hub_df
from distance_matrix_calculation import hubs_gdf

##########################################
###### GENERATE SITE CAPACITY DATA
# %%codecell
#https://ccpia.org/occupancy-load-signs/
occ_limits = pd.DataFrame({'cat_site':['W', 'CC', 'Pri', 'Sec', 'Coll'], 'sqft_pp':[15, 15, 50, 50, 50]})

hub_occ_df = pd.merge(hubs_gdf, occ_limits, on = 'cat_site')
hub_occ_df['occ_site'] = hub_occ_df['SQFT_ROOF']/hub_occ_df['sqft_pp']
hub_occ_df = hub_occ_df.loc[:, ['id_site', 'cat_site', 'occ_site']]

##########################################
###### DEFINE MODEL
# %%codecell
model = ConcreteModel()

model.dist_to_hub_df = dist_to_hub_df
model.hub_occ_df = hub_occ_df

model.max_dist = 1.5
model.max_hubs = 5

model.cengeos = Set(initialize = dist_to_hub_df.index)
model.hubs = Set(initialize = dist_to_hub_df.columns)

##########################################
###### DEFINE PARAMETERS AND ATTACH TO MODEL
# %%codecell
def set_distance(model, cengeo, hub):
    return model.dist_to_hub_df.loc[cengeo, hub]

model.distances = Param(model.cengeos, model.hubs, initialize = set_distance)
model.distances.pprint()

def set_capacities(model, hub):
    return model.hub_occ_df.loc[hub]

model.capacity = Param(model.hubs, initialize = set_capacities)

##########################################
###### DEFINE VARIABLES AND ATTACH TO MODEL
# %%codecell
model.ishub = Var(model.hubs, within=Binary)
model.ishub.pprint()


model.capacities = Param(model.hubs,initialize = set_capacities)
model.capacities.pprint()

def max_capacity(model, hub):
    return sum(model.fraction[blockgroup,hub]*model.population[blockgroup] for blockgroup in model.blockgroups) <= model.capacities[hub])
model.demand = Constraint(model.hubs, rule=max_capacity)


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
