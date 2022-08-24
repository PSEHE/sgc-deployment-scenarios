# This script compares overall driving - walking distances from hubs to block group
# centroids, and particularly compares walking and driving routes for the five
# longest driving routes.

import osmnx as ox
from osmnx import utils_graph
import networkx as nx

import geopandas as gpd
import pandas as pd
import numpy as np
from statistics import mean

import matplotlib.pyplot as plt
import plotly.express as px
import shapely
import folium
import plotly.graph_objects as go # or plotly.express as px

import os

import sklearn
import pyproj
from scipy.sparse import csr_matrix
from shapely.ops import linemerge

import warnings

from distance_matrix_functions_cmm import *

# Compare sparse distance matrices for differences
walk_csv = pd.read_csv(r'data/distance_matrices/distmatrix_walk_contracosta.csv').set_index('Unnamed: 0')
walk_csv.index.names = [None]
drive_csv = pd.read_csv(r'data/distance_matrices/distmatrix_contracosta.csv').set_index('Unnamed: 0')
drive_csv.index.names = [None]
#walk_csv_edited = pd.read_csv(r'data/distance_matrices/distmatrix_walk_cfcontracosta.csv').set_index('Unnamed: 0')
#walk_csv_edited.index.names = [None]
#walk_csv_edited = pd.read_csv(r'data/distance_matrices/distmatrix_walk_cfcontracosta.csv').set_index('Unnamed: 0')
walk_csv_edited = pd.read_csv(r'data/distance_matrices/distmatrix_walk_wilmington.csv').set_index('Unnamed: 0')
walk_csv_edited.index.names = [None]
#walk_csv_transit = pd.read_csv(r'data/distance_matrices/distmatrix_walk_cf_transit_contracosta.csv').set_index('Unnamed: 0')
walk_csv_transit = pd.read_csv(r'data/distance_matrices/distmatrix_walk_transit_wilmington.csv').set_index('Unnamed: 0')
walk_csv_transit.index.names = [None]
# Calculate the number of differences (walking vs driving)
walk_tf = walk_csv.notna()
drive_tf = drive_csv.notna()
(~walk_tf.eq(drive_tf)).sum().sum()

# Graph sparse matrices (walking vs driving)
drive_sparse = drive_csv.fillna(0)
walk_sparse = walk_csv.fillna(0)
plt.spy(walk_sparse)
plt.spy(drive_sparse)

# Calculate the number of differences (walking vs custom filter + overpass take out)
walk_tf = walk_csv.notna()
walk_cf_tf = walk_csv_edited.notna()
(~walk_tf.eq(walk_cf_tf)).sum().sum()

# Graph sparse matrices (walking vs custom filter)
walk_cf_sparse = walk_csv_edited.fillna(0)
walk_sparse = walk_csv.fillna(0)
plt.spy(walk_sparse)
plt.spy(walk_cf_sparse)

# Graph distances walking vs driving
fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(drive_csv,walk_csv)
plt.xlabel("Driving Distance")
plt.ylabel("Walking Distance")
plt.xlim(0, 25)
plt.ylim(0, 25)
plt.plot(range(25), color = 'black')
plt.show()


# Graph distances walking vs walking (cf)
fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(walk_csv,walk_csv_edited)
plt.xlabel("Walking Distance")
plt.ylabel("Walking (Custom Filter + No Underpasses) Distance")
plt.xlim(0, 25)
plt.ylim(0, 25)
plt.plot(range(25), color = 'black')
plt.show()

# Graph distances walking (cf) vs walking (cf+transit
fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(walk_csv_edited,walk_csv_transit)
plt.xlabel("Walking Distance (Custom Filter)")
plt.ylabel("Walking (Custom Filter + Transit) Distance")
#plt.xlim(0, 1)
#plt.ylim(0, 1290)
plt.axline((0, 0), slope = 1/.00077767, color = 'black')
#plt.plot(range(25), color = 'black')
plt.show()

# count distances that are included/excluded in walking vs transit + Walking
walk_new = walk_csv_edited.copy()
walk_new[walk_new < 1] = None # get all distances greater than 1 mile
transit_new = walk_csv_transit.copy()
transit_new[transit_new > 1290] = None # keep all distances less than 1290 seconds
walk_new = walk_new.notna()
transit_new = transit_new.notna()
(np.logical_and(walk_new, transit_new)).sum().sum()

walk_new = walk_csv_edited.copy()
walk_new[walk_new >= 1] = None # get all distances less than 1 mile
transit_new = walk_csv_transit.copy()
transit_new[transit_new <= 1290] = None # keep all distances greater than 1290 seconds
walk_new = walk_new.notna()
transit_new = transit_new.notna()
(np.logical_and(walk_new, transit_new)).sum().sum()

# Investigate a long driving distance/short walking distance point
# load graphs
county = 'contracosta'
drive = ox.load_graphml(os.path.join(os.getcwd(), 'data/graphs/graph_' + county + '.graphml'))
walk = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + county + '.graphml'))
cf = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf' + county + '.graphml'))

# find long driving/short walking point
# function to return the row and column names of the nth maximum value of a matrix
def find_max_pos(data, n):
    stack = data.stack()
    max = stack.sort_values(ascending=False).head(n)
    max = max.tail(1).unstack()
    return [max.columns[0], max.index[0]]

# function that takes resilience hub or block group data and id,
# and returns coordinates of hub or block group corresponding to id
def locate(data, id, col):
    row = data.loc[data[col] == id]
    return [row['LAT'].iloc[0], row['LON'].iloc[0]]

# Function that takes origin node, destination node, graph, and creates MultiLineString shortest path
def create_shortest_path(orig_node, dest_node, graph):
    route = nx.shortest_path(graph, orig_node, dest_node)
    route_attributes = ox.utils_graph.get_route_edge_attributes(graph, route)
    results = []
    for item in route_attributes:
        results.append(item['geometry'])
    return linemerge(results)

# function that takes a hub ID and block group code,
# and plots walking and driving routes between them
def plot_routes(site, bg, site_data, bg_data):
    bg_pt = locate(bg_data, bg, 'GISJOIN')
    site_pt = locate(site_data, site, 'id_site')

    orig_node = get_coords_and_nearest_node(bg, 'GISJOIN', bg_data, drive)
    dest_node = get_coords_and_nearest_node(site, 'id_site', site_data, drive)
    drive_path = create_shortest_path(orig_node, dest_node, drive)

    orig_node = get_coords_and_nearest_node(bg, 'GISJOIN', bg_data, walk)
    dest_node = get_coords_and_nearest_node(site, 'id_site', site_data, walk)
    walk_path = create_shortest_path(orig_node, dest_node, walk)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlabel('X coordinate', fontsize=15)
    ax.set_ylabel('Y coordinate', fontsize=15)
    ax.plot(*drive_path.xy, label='Drive')
    ax.plot(*walk_path.xy, label='Walk')
    ax.scatter(x = bg_pt[1], y = bg_pt[0], label = 'BG Centroid', color = 'red')
    ax.scatter(x = site_pt[1], y = site_pt[0], label = 'Site', color = 'purple')
    ax.set_aspect('equal', adjustable='box')
    plt.legend()

# MAPBOX ATTEMPT -- DOES NOT WORK RIGHT NOW
# bg_data = bgs_pt_gdf
# site_data = sites_gdf
# site = pt_1[0]
# bg = pt_1[1]
# bg_pt = locate(bg_data, bg, 'GISJOIN')
# site_pt = locate(site_data, site, 'id_site')
#
# orig_node = get_coords_and_nearest_node(bg, 'GISJOIN', bg_data, drive)
# dest_node = get_coords_and_nearest_node(site, 'id_site', site_data, drive)
# drive_path = create_shortest_path(orig_node, dest_node, drive)
#
# px.set_mapbox_access_token(open(".mapbox_token").read())
#
# df = px.data.carshare()
# fig = px.scatter_mapbox(df,
#                         lon = df['centroid_lon'],
#                         lat = df['centroid_lat'],
#                         zoom = 3,
#                         color = df['peak_hour'],
#                         width = 1200,
#                         height = 900)
# fig.update_layout(mapbox_style = "open-street-map")
# fig.show()
# fig_map = go.Figure(go.Scattermapbox(lat=hubs_built_df["LAT"], lon=hubs_built_df["LON"],
#                                  mode='markers',
#                                 marker=go.scattermapbox.Marker(
#                                     size=20*np.sqrt(hubs_built_df["kw_occ"])/np.max(np.sqrt(hubs_built_df["kw_occ"])),
#                                     color='rgb(255, 0, 0)',
#                                     opacity=0.7,
#                                     # symbol = "castle"
#                                 ),
#                                 name = "Built Hubs",
#                                 # marker_symbol = 'circle-open',
#                                 text=hubs_built_df["name_site"],
#                                 hoverinfo='text'
#                                  # hovertext=hubs_df["name_site"],
#                                  # hover_data=["cat_site"],
#                                  # color_discrete_sequence=["fuchsia"],
#                                  # zoom=5,
#                                  # height=600
#                                  )
#                 )

# USING FUNCTIONS
ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4629'
wgs84 = 'EPSG:4326'

# Building candidate sites GeoDataFrame
sites_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'candidate_sites_campuses.csv')
sites_df_raw = pd.read_csv(sites_path)
sites_df_raw = sites_df_raw.loc[sites_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]
sites_geom = gpd.points_from_xy(sites_df_raw.LON, sites_df_raw.LAT, crs = nad83)
sites_gdf = gpd.GeoDataFrame(sites_df_raw, geometry = sites_geom, crs = nad83)

# Building block group GeoDataFrame
bgs_path = os.path.join(os.getcwd(), 'data', 'bg_ca_19', 'shp', 'blockgroup_CA_19.shp')
bgs_gdf = gpd.read_file(bgs_path)
bgs_gdf = bgs_gdf.to_crs(sites_gdf.crs)
bgs_lons = [float(intpt) for intpt in bgs_gdf['INTPTLON']]
bgs_lats = [float(intpt) for intpt in bgs_gdf['INTPTLAT']]
bgs = pd.DataFrame(bgs_gdf[['GISJOIN', 'COUNTYFP']])
bgs['LON'] = bgs_lons
bgs['LAT'] = bgs_lats
bgs_pt_geom = gpd.points_from_xy(x = bgs.LON,y = bgs.LAT, crs = nad83)
bgs_pt_gdf = gpd.GeoDataFrame(bgs, geometry = bgs_pt_geom, crs = nad83)

# Get top 5 longest driving block group centroid/site code pairs
pt_1 = find_max_pos(drive_csv, 1)
pt_2 = find_max_pos(drive_csv, 2)
pt_3 = find_max_pos(drive_csv, 3)
pt_4 = find_max_pos(drive_csv, 4)
pt_5 = find_max_pos(drive_csv, 5)

locate(bg_data, pt_2[1], 'GISJOIN')
locate(site_data, pt_5[0], 'id_site')

# Plot routes and sites
plot_routes(pt_1[0], pt_1[1], sites_gdf, bgs_pt_gdf)
plot_routes(pt_2[0], pt_2[1], sites_gdf, bgs_pt_gdf)
plot_routes(pt_3[0], pt_3[1], sites_gdf, bgs_pt_gdf)
plot_routes(pt_4[0], pt_4[1], sites_gdf, bgs_pt_gdf)
plot_routes(pt_5[0], pt_5[1], sites_gdf, bgs_pt_gdf)

# Retrieve lat/lon pairs to check route length against Google Maps
pt_6 = find_max_pos(drive_csv, 400)
pt_7 = find_max_pos(drive_csv, 450)
pt_8 = find_max_pos(drive_csv, 500)
pt_9 = find_max_pos(drive_csv, 550)
pt_10 = find_max_pos(drive_csv, 600)

def print_info(pt):
    walk_dist = walk_csv.loc[pt[1]][pt[0]]
    drive_dist = drive_csv.loc[pt[1]][pt[0]]

    bg_loc = locate(bg_data, pt[1], 'GISJOIN')
    site_loc = locate(site_data, pt[0], 'id_site')
    return [walk_dist, drive_dist, bg_loc, site_loc]

print_info(pt_6)
print_info(pt_7)
print_info(pt_8)
print_info(pt_9)
print_info(pt_10)
