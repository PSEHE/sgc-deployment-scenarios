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
import numpy as np
import os
import shapely

place_name = "Contra Costa County, California, USA"
max_D = 100
####### COMMENTED OUT FOLLOWING TWO LINES ARE FOR CHOOSING NEW GRAPH ###########
# graph = ox.graph_from_place(place_name, network_type='drive')
# ox.io.save_graphml(graph,os.path.join(os.getcwd(),"./data/",place_name))
graph = ox.io.load_graphml(os.path.join(os.getcwd(),"./data/",place_name))
# Load in candidate sites
hubs = pd.read_csv(os.path.join(os.getcwd(),"./data/candidate_site_campuses_2021-11-17/candidate_site_campuses.csv"))
hubs = hubs[hubs["cat_site"]!="X"]
hubs_gdf = gpd.GeoDataFrame(hubs[["id_site","SQFT_ROOF","LON","LAT"]],
                            geometry=gpd.points_from_xy(hubs.LON, hubs.LAT),
                            crs = "epsg:4326")
bg_gdf = gpd.read_file(os.path.join(os.getcwd(),"./data/bg_ca_19/blockgroup_CA_19.shp"))
bg_gdf = bg_gdf.to_crs(hubs_gdf.crs)
# impute speed on all edges missing data
graph = ox.add_edge_speeds(graph)
# calculate travel time (seconds) for all edges
graph = ox.add_edge_travel_times(graph)
# %% codecell
graph_proj = ox.project_graph(graph)
nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)
fig, ax = ox.plot_graph(ox.project_graph(graph))
# %% codecell
# Now to only consider hubs and blockgroups within above graph...
 # (temporary step for debugging just one county before doing all of California)
min_lon = nodes_proj["lon"].min()
max_lon = nodes_proj["lon"].max()
min_lat = nodes_proj["lat"].min()
max_lat = nodes_proj["lat"].max()
bb_polygon = shapely.geometry.Polygon([(min_lon,min_lat),
                      (min_lon,max_lat),
                      (max_lon,max_lat),
                      (max_lon,min_lat)])
hubs_gdf = hubs_gdf[hubs_gdf.within(bb_polygon)]
bg_gdf = bg_gdf[bg_gdf.centroid.within(bb_polygon)]
# %% codecell

# distance_matrix = pd.DataFrame(np.nan,index = bg_gdf["GISJOIN"],columns = hubs["id_site"]
distance_matrix = np.NaN*np.zeros((len(bg_gdf),len(hubs_gdf))) # Initialize array to keep track of distances
# Calculating distances between hubs and block groups
for census_lat,census_lon,bg_idx in zip(bg_gdf["INTPTLAT"],bg_gdf["INTPTLON"],range(len(bg_gdf))):
    # Find all hubs within max_D km
    # TODO: MODIFY FOLLOWING LOOP TO ONLY DO CLOSEBY HUB
    for hub_lat,hub_lon,hub_idx in zip(hubs_gdf["LAT"],hubs_gdf["LON"],range(len(hubs_gdf))):
        distance_matrix[bg_idx,hub_idx] = 5

distance_matrix_df = pd.DataFrame(distance_matrix, index=bg_gdf["GISJOIN"],columns = hubs_gdf["id_site"])












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
