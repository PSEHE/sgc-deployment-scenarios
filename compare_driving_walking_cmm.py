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
import shapely
import folium

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

# Calculate the number of differences
walk_tf = walk_csv.notna()
drive_tf = drive_csv.notna()
(~walk_tf.eq(drive_tf)).sum().sum()

# Graph sparse matrices
drive_sparse = drive_csv.fillna(0)
walk_sparse = walk_csv.fillna(0)
plt.spy(walk_sparse)
plt.spy(drive_sparse)

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

# Investigate a long driving distance/short walking distance point
# load graphs
county = 'contracosta'
drive = ox.load_graphml(os.path.join(os.getcwd(), 'data/graphs/graph_' + county + '.graphml'))
walk = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + county + '.graphml'))
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
    #ax.axis('equal')
    plt.legend()

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
