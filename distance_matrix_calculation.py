# %% markdown
# PROGRESS: File below loads in condidate sites, block group geometries and,
# graph of Contra Costa county.
# NEXT STEPS: Write for loop that will.
# 1. Find all hubs that are within max_D of a given block group
# 2. Start nested for loop inside to calculate travel time between hubs and blockgroups

# %% codecell
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

place_name = "Contra Costa County, California, USA"
max_D = 100
####### COMMENTED OUT FOLLOWING TWO LINES FOR CHOOSING NEW GRAPH ###########
# graph = ox.graph_from_place(place_name, network_type='drive')
# ox.io.save_graphml(graph,"./data/"+place_name)
graph = ox.io.load_graphml("./data/"+place_name)
# Load in candidate sites
hubs = pd.read_csv(r"C:\Users\yunus\github\sgc-deployment-scenarios\data\candidate_site_campuses_2021-11-17\candidate_site_campuses.csv")
hubs = hubs[hubs["cat_site"]!="X"]
hubs_gdf = gpd.GeoDataFrame(hubs[["id_site","SQFT_ROOF"]], geometry=gpd.points_from_xy(hubs.LON, hubs.LAT))
bg_gdf = gpd.read_file(r"C:\Users\yunus\github\sgc-deployment-scenarios\data\bg_ca_19\blockgroup_CA_19.shp")
# impute speed on all edges missing data
graph = ox.add_edge_speeds(graph)
# calculate travel time (seconds) for all edges
graph = ox.add_edge_travel_times(graph)

# %% codecell
fig, ax = ox.plot_graph(ox.project_graph(graph))
graph_proj = ox.project_graph(graph)
nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)
# %% codecell
# Calculating distances between hubs and block groups
for census_lat,census_lon in zip(bg_gdf["INTPTLAT"],bg_gdf["INTPTLON"]):
    # Find all hubs within max_D km

    for hub_lat,hub_lon in zip(hubs_gdf["INTPTLAT"],hubs_gdf["INTPTLON"]):










########### OLD CODE BELOW ###########################


#
# # %% codecell
# import numpy as np
# np.sum(edges_proj.isna()["travel_time"])
# edges_proj
# # %% codecell
# from shapely.geometry import box
# bbox = box(*edges_proj.unary_union.bounds)
# orig_point = bbox.centroid
# nodes_proj['x'] = nodes_proj.x.astype(float)
# maxx = nodes_proj['x'].max()
# target_loc = nodes_proj.loc[nodes_proj['x']==maxx, :]
# target_point = target_loc.geometry.values[0]
# orig_xy = (orig_point.y, orig_point.x)
# target_xy = (target_point.y, target_point.x)
# orig_node = ox.get_nearest_node(graph_proj, orig_xy, method='euclidean')
# target_node = ox.get_nearest_node(graph_proj, target_xy, method='euclidean')
# o_closest = nodes_proj.loc[orig_node]
# t_closest = nodes_proj.loc[target_node]
# od_nodes = gpd.GeoDataFrame([o_closest, t_closest], geometry='geometry', crs=nodes_proj.crs)
#
#
# route = nx.shortest_path(G=graph_proj, source=orig_node, target=target_node, weight='length')
#
#
# fig, ax = ox.plot_graph_route(graph_proj, route)
#
# # %% codecell
# import time
#
# t_start = time.process_time()
#
# for _ in range(0,10):
#     route = nx.shortest_path(G=graph_proj, source=orig_node, target=target_node, weight='length')
#
# t_end = time.process_time()
#
# (t_end-t_start)/10
#
# # %% codecell
