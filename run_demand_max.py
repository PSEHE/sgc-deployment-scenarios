# %% markdown
# # Overview
# Here, I want to run a set of simulations in which the model tries to maximize the demand met within a certain distance.
# It is limited by the number of hubs it can build and the capactiy of each hub
# Variables to change:
# 1. Number of hubs to build
# 2. Maximum distance for demand
# I suspect that, as I change the maximum distance, hubs will become more centralized near populated blockgroups and may not fill to capacity

# To visualize this, I will plot the following.
# 1. Histogram of the fraction of capacity of hubs
# 2. Histogram of the fraction of blockgroup demand met
# 3. Histogram or CDF of the probability of distance travelled
# 4.
# %% markdown

# %% codecell
import pandas as pd
import numpy as np
import geopandas as gpd
import os
import importlib
from data_cleaning import hub_occ_dict
from data_cleaning import hub_sqft_dict
from data_cleaning import heatdays_df
from data_cleaning import cengeo_pop_dict
from data_cleaning import bg_ces_df
bg_ces_df.columns


dist_to_hub_df = pd.read_csv('data/distmatrix_bbox.csv')
dist_to_hub_df.set_index("Unnamed: 0",inplace = True)
# %% codecell
import demand_maximization_models as dem_models
importlib.reload(dem_models)
max_hubs_list =[50,100,150]
max_distance_list = [1,3,5]

prop_served_dict = dict()
hub_yn_dict = dict()

for max_hubs in max_hubs_list:
    for max_distance in max_distance_list:
        prop_served_dict[(max_hubs,max_distance)], hub_yn_dict[(max_hubs,max_distance)] = dem_models.build_demand_max_model(max_hubs,
                                   max_distance,
                                   dist_to_hub_df,
                                   hub_sqft_dict,
                                   cengeo_pop_dict,
                                   hub_occ_dict,
                                   bg_ces_df)
        run_string = "Contra_"+str(max_hubs)+"hubs"+str(max_distance)+"miles_max"
        try:
            os.mkdir(os.path.join("results",run_string))
        except OSError as error:
            print(error)
        prop_served_dict[(max_hubs,max_distance)].to_csv(os.path.join("results",
                                                                      run_string,
                                                                      "var_prop_served.csv"))
        hub_yn_dict[(max_hubs,max_distance)].to_csv(os.path.join("results",
                                                                 run_string,
                                                                 "var_hub_yn.csv"))


# run_string = "p_med_min_block_125"

# %% codecell
import matplotlib.pyplot as plt
fig, axs = plt.subplots(1,3,figsize = (8,6),dpi=300)
axs_counter = 0
for max_hubs in max_hubs_list:
    prop_df = pd.DataFrame()
    for max_distance in max_distance_list:
        prop_served = prop_served_dict[(max_hubs,max_distance)]
        prop_df[max_distance] = prop_served.sum(axis=1)
        # hub_yn = hub_yn_dict[(max_hubs,max_distance)]
        # hub_capacities = []
        # axs[axs_counter//3, axs_counter%3].hist(prop_served.sum(axis=1),
        #                                         label = max_distance,
        #                                         stacked=False
        #                                         # histtype=u'step'
        #                                         )
    axs[axs_counter//3, axs_counter%3].hist(prop_df,
                                            label = prop_df.columns,
                                            stacked=False
                                            # histtype=u'step'
                                            )
    # prop_df.hist(stacked=False,ax = axs[axs_counter//3, axs_counter%3])
    axs[axs_counter//3, axs_counter%3].set_title("Hubs = " + str(max_hubs))
    axs[axs_counter//3, axs_counter%3].legend(title="max_distance",loc='upper center')
    axs[axs_counter//3, axs_counter%3].set_ylim((0,550))
    axs_counter += 1
plt.tight_layout()
plt.savefig("Proportion_served_hist.png")
# axs[0,1].plot([5,6])
        #
        # for hub in prop_served.columns:
        #     for bg in prop_served.columns:
        #         prop_served.sum(axis=1).unique()
        #         prop_served = prop_served_dict[(max_hubs,max_distance)]

# %% codecell
import matplotlib.pyplot as plt
fig, axs = plt.subplots(2,3,figsize = (8,6),dpi=300)
axs_counter = 0
for max_hubs in max_hubs_list:
    prop_df = pd.DataFrame()
    capacities = []
    for max_distance in max_distance_list:
        prop_served = prop_served_dict[(max_hubs,max_distance)].copy()
        prop_df[max_distance] = prop_served.sum(axis=1)
        hub_yn = hub_yn_dict[(max_hubs,max_distance)].copy()
        # hub_yn = hub_yn[hub_yn==1]
        # hub_yn = hub_yn.take(hub_yn==1)
        hub_yn = hub_yn.join(pd.Series(hub_occ_dict,name="Capacity"))
        # hub_yn[hub_yn[0]==1].hist(column = ["Capacity"],
        #                             ax = [axs_counter//3, axs_counter%3])
        # capacities[str(max_distance)] = hub_yn[hub_yn[0]==1]["Capacity"].to_numpy()
        capacities.append(hub_yn[hub_yn[0]==1]["Capacity"].to_numpy())

    axs[axs_counter//3, axs_counter%3].hist(capacities,density=True,label = max_distance_list)
        # hub_capacities = []
        # axs[axs_counter//3, axs_counter%3].hist(prop_served.sum(axis=1),
        #                                         label = max_distance,
        #                                         stacked=False
        #                                         # histtype=u'step'
        #                                         )
    # axs[axs_counter//3, axs_counter%3].hist(prop_df,
    #                                         label = prop_df.columns,
    #                                         stacked=False
    #                                         # histtype=u'step'
    #                                         )
    # prop_df.hist(stacked=False,ax = axs[axs_counter//3, axs_counter%3])
    axs[axs_counter//3, axs_counter%3].set_title("Hubs = " + str(max_hubs))
    axs[axs_counter//3, axs_counter%3].legend(title="max_distance",loc='upper right')
    # axs[axs_counter//3, axs_counter%3].set_ylim((0,100))
    axs_counter += 1
plt.tight_layout()
plt.savefig("Hub_capacities_built.png")
# %% codecell
# %% codecell
# %% codecell
# %% codecell
# %% codecell
