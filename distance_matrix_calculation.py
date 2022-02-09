# %% codecell
import osmnx as ox
from osmnx import utils_graph
import networkx as nx

import geopandas as gpd
import pandas as pd
import numpy as np
from statistics import mean

import matplotlib.pyplot as plt
import shapely
import folium

import os

##########################################
# %% codecell
location = 'Contra Costa County, California, USA'
richmond_center = [37.943882, -122.35342]

ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4629'

wgs84 = 'EPSG:4326'

##########################################
# %% codecell
def plot_gdf_with_background(gdf, zoom=12, center = None):

    if center is not None:
        map_center = center
    else:
        map_center_lon = gdf['geometry'].x.mean()
        map_center_lat = gdf['geometry'].y.mean()
        map_center = [map_center_lat, map_center_lon]

    map_with_background = folium.Map(map_center, zoom_start = zoom, width = '50%', height = '50%', tiles = 'OpenStreetMap')

    folium.GeoJson(gdf).add_to(map_with_background)

    return(map_with_background)


######### READ IN AND CLEAN NECESSARY DATA

##########################################
# %% codecell
import warnings

warnings.filterwarnings('ignore')

graph_raw = ox.graph_from_place(location, network_type = 'drive', simplify = True)

graph = ox.project_graph(graph_raw, to_crs = nad83)
graph = ox.speed.add_edge_speeds(graph)
graph = ox.speed.add_edge_travel_times(graph)

graph_nodes_gdf, graph_edges_gdf = ox.graph_to_gdfs(graph, nodes = True, edges = True)

graph_edges_gdf_reset = graph_edges_gdf.reset_index()
graph_edges_gdf_reset.rename(columns = {'u':'from_node', 'v':'to_node'}, inplace = True)

#ox.plot_graph(graph)
##########################################
# %% codecell
hubs_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'candidate_sites_campuses.csv')

hubs_df_raw = pd.read_csv(hubs_path)
hubs_df_raw = hubs_df_raw.loc[hubs_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]

hubs_geom = gpd.points_from_xy(hubs_df_raw.LON, hubs_df_raw.LAT, crs = nad83)
hubs_gdf = gpd.GeoDataFrame(hubs_df_raw, geometry = hubs_geom, crs = nad83)

#plot_gdf_with_background(hubs_gdf, 13, richmond_center)

##########################################
# %% codecell
cengeos_path = os.path.join(os.getcwd(), 'data', 'bg_ca_19', 'blockgroup_CA_19.shp')

cengeos_gdf = gpd.read_file(cengeos_path)
cengeos_gdf = cengeos_gdf.to_crs(hubs_gdf.crs)

cengeos_lons = [float(intpt) for intpt in cengeos_gdf['INTPTLON']]
cengeos_lats = [float(intpt) for intpt in cengeos_gdf['INTPTLAT']]

cengeos = pd.DataFrame(cengeos_gdf[['GISJOIN', 'COUNTYFP']])
cengeos['LON'] = cengeos_lons
cengeos['LAT'] = cengeos_lats

cengeos_pt_geom = gpd.points_from_xy(x = cengeos.LON,y = cengeos.LAT, crs = nad83)
cengeos_pt_gdf = gpd.GeoDataFrame(cengeos, geometry = cengeos_pt_geom, crs = nad83)

#plot_gdf_with_background(cengeos_pt_gdf, 13, richmond_center)

##### RESTRICT TO HUBS WITHIN DESIRED AREA

##########################################
# %% codecell
lon_max = graph_nodes_gdf['lon'].max()
lon_min = graph_nodes_gdf['lon'].min()
lon_avg = (lon_max + lon_min)/2

lat_max = graph_nodes_gdf['lat'].max()
lat_min = graph_nodes_gdf['lat'].min()
lat_avg = (lat_min + lat_max)/2

bbox_coords = [(lon_min, lat_min), (lon_min, lat_max), (lon_max, lat_max), (lon_max, lat_min)]
bbox_poly = shapely.geometry.Polygon(bbox_coords)

##########################################
# %% codecell
hubs_gdf_bbox = hubs_gdf[hubs_gdf.within(bbox_poly)]

#plot_gdf_with_background(hubs_gdf_bbox)

##########################################
# %% codecell
cengeos_pt_gdf_bbox = cengeos_pt_gdf[cengeos_pt_gdf.within(bbox_poly)].reset_index(drop = True)

#plot_gdf_with_background(cengeos_pt_gdf_bbox, center = richmond_center)

##########################################
# %% codecell
cengeos_pt_gdf_bbox_proj = cengeos_pt_gdf_bbox.to_crs(ca_albers_nad83)

one_mile = 5280
cengeos_buffer = cengeos_pt_gdf_bbox_proj.buffer(one_mile*5)

cengeos_buffer_gdf_bbox = gpd.GeoDataFrame(cengeos_pt_gdf_bbox['GISJOIN'])
cengeos_buffer_gdf_bbox['geometry'] = cengeos_buffer

cengeos_buffer_gdf_bbox = cengeos_buffer_gdf_bbox.to_crs(nad83)

#### BUILD DISTANCE MATRIX FOR DESIRED AREA

##########################################
# %% codecell
n_cengeos = len(cengeos_pt_gdf_bbox)
n_hubs = len(hubs_gdf_bbox)

##########################################
# %% codecell
name_index = {i:cengeos_pt_gdf_bbox.iloc[i]['GISJOIN'] for i in range(0, n_cengeos)}
name_columns = {i:hubs_gdf_bbox.iloc[i]['id_site'] for i in range(0, n_hubs)}

dist_to_hub_matrix = np.NaN*np.zeros((len(cengeos_pt_gdf_bbox), len(hubs_gdf_bbox)))
dist_to_hub_df = pd.DataFrame(dist_to_hub_matrix)

dist_to_hub_df.rename(index = name_index, columns = name_columns, inplace = True)

##########################################
# %% codecell
def get_coords_and_nearest_node(in_pt, in_colname, in_pt_gdf, in_graph=graph):

    pt_geom = in_pt_gdf.loc[in_pt_gdf[in_colname] == in_pt, 'geometry']
    pt_coords = [float(pt_geom.y), float(pt_geom.x)]
    pt_nearest_node = ox.get_nearest_node(in_graph, pt_coords, method = 'euclidean')

    return(pt_nearest_node)

def get_nearby_hubs(in_cengeo, in_cengeo_buffers=cengeos_buffer_gdf_bbox, in_hubs=hubs_gdf_bbox):

    cengeo_buffer = in_cengeo_buffers.loc[in_cengeo_buffers['GISJOIN'] == in_cengeo, 'geometry'].reset_index(drop = True)[0]
    cengeo_nearest_hubs = in_hubs[in_hubs.within(cengeo_buffer)]

    return(cengeo_nearest_hubs)

def get_steps_in_route(in_route):

    steps_in_route = []

    for i in range(0, len(in_route)):
        steps_in_route.append([in_route[i-1], in_route[i]])

    steps_in_route = steps_in_route[1:]

    return(steps_in_route)

def get_travel_time(in_steps, in_edges=graph_edges_gdf_reset):

    travel_times_sec = []

    for step in range(0, len(in_steps)):

        step_in_route = in_steps[step]
        step_duration_sec = in_edges.loc[(in_edges['from_node'] == step_in_route[0]) & (in_edges['to_node'] == step_in_route[1])]['travel_time']
        travel_times_sec.append(step_duration_sec)

    travel_times_min = [float(travel_time)/60 for travel_time in travel_times_sec]
    travel_time_min = round(sum(travel_times_min), 2)

    return(travel_time_min)

##########################################
# %% codecell
cengeos_bbox = cengeos_pt_gdf_bbox.loc[:, 'GISJOIN']
no_path_founds = []

for cengeo in cengeos_bbox:

    node_origin = get_coords_and_nearest_node(cengeo, 'GISJOIN', cengeos_pt_gdf_bbox)
    hubs_nearby_gdf = get_nearby_hubs(cengeo)
    hubs_nearby = hubs_nearby_gdf.loc[:, 'id_site']

    for hub in hubs_nearby:

        node_target = get_coords_and_nearest_node(hub, 'id_site', hubs_gdf_bbox)

        try:
            travel_dist_m = nx.shortest_path_length(graph, node_origin, node_target, weight = 'length')
            dist_to_hub_df.loc[cengeo, hub] = round(travel_dist_m/1609.344, 2)
        except:
            dist_to_hub_df.loc[cengeo, hub] = None
            no_path_founds.append((cengeo, hub))
