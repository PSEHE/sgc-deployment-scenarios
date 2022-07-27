# Plotting various sidewalk filters for Richmond and Wilmington

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

import warnings
import distance_matrix_functions_cmm
from distance_matrix_functions_cmm import *

import importlib
importlib.reload(distance_matrix_functions_cmm)

## ------------------------------ RICHMOND -------------------------------------
# Understanding what various filters would do for the sidewalks in Contra Costa
place = 'Richmond, California'

# taking out steps, footway, service, path, adding in secondary, take out foot != no
cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
        ["highway"~"pedestrian|living_street|tertiary|secondary|residential"]["service"!~"private"]{}''')\
    .format(ox.settings.default_access)

G_orig = ox.graph_from_place(place, network_type = "walk")
G_walk = ox.graph_from_place(place, custom_filter=cf_orig)
G_cf = ox.graph_from_place(place, custom_filter=cf_adj2)

print(len(G_orig), 'original')
print(len(G_walk), 'custom filter')
print(len(G_sidewalk), 'sidewalk')

ax = ox.plot_graph(G_orig, edge_color = 'w', node_size = 0)
ax = ox.plot_graph(G_walk, edge_color = 'w', node_size = 0)
ax = ox.plot_graph(G_sidewalk, edge_color = 'w', node_size = 0)

## ------------------------------ CONTRA COSTA -------------------------------------
ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4269'
wgs84 = 'EPSG:4326'

# Read in county boundaries
county_gdf = gpd.read_file(os.path.join("data","cb_2018_us_county_500k.zip"))
county_gdf = county_gdf[county_gdf["STATEFP"]=='06'] #Just california

# Getting county FIPS codes
county_graph_buffer = 0.1 # Add on this distance to get street nodes/edges from neighboring counties too.
county = 'Contra Costa';county_fips = '013'

output_county = county.lower().replace(' ', '')
# Get graph for county
county_bbox = county_gdf.loc[county_gdf["COUNTYFP"]==county_fips,'geometry'].unary_union
county_bbox_buffered = county_bbox.buffer(county_graph_buffer)
county_graph = get_county_walk_graph_from_polygon(county_bbox, nad83, cf = True)
ax = ox.plot_graph(county_graph, edge_color = 'w', node_size = 0)

walk_graph = get_county_walk_graph_from_polygon(county_bbox, nad83)
ax = ox.plot_graph(walk_graph, edge_color = 'w', node_size = 0)

# ## ------------------------------ RICHMOND -------------------------------------
# # Trying out different filters for sidewalk data
# place = 'Richmond, California'
#
# cf= ('''["area"!~"yes"]["highway"~"footway|pedestrian|path|steps|living_street|
#         tertiary|residential|service"]["foot"!~"no"]["service"!~"private"]{}''')\
#     .format(ox.settings.default_access)
# cf_sidewalk=('["footway"~"sidewalk"]{}').format(ox.settings.default_access)
# G_orig = ox.graph_from_place(place, network_type = "walk")
# G_walk = ox.graph_from_place(place, custom_filter=cf)
# G_sidewalk = ox.graph_from_place(place, custom_filter=cf_sidewalk)
# print(len(G_orig), 'original')
# print(len(G_walk), 'custom filter')
# print(len(G_sidewalk), 'sidewalk')
#
# ax = ox.plot_graph(G_orig, edge_color = 'w', node_size = 0)
# ax = ox.plot_graph(G_walk, edge_color = 'w', node_size = 0)
# ax = ox.plot_graph(G_sidewalk, edge_color = 'w', node_size = 0)
#
# ## --------------------------- WILMINGTON --------------------------------------
# # Trying out different filters for sidewalk data
# wilmington_path = os.path.join(os.getcwd(), 'data', 'LA_Times_Neighborhood_Boundaries', 'LA_Times_Neighborhood_Boundaries.shp')
# wilmington_gdf = gpd.read_file(wilmington_path)
# shp = wilmington_gdf['geometry'].unary_union
# shp
# cf= ('''["area"!~"yes"]["highway"~"footway|pedestrian|path|steps|living_street|
#         tertiary|residential|service"]["foot"!~"no"]["service"!~"private"]{}''')\
#     .format(ox.settings.default_access)
# cf_sidewalk=('["footway"~"sidewalk"]{}').format(ox.settings.default_access)
# G_orig = ox.graph_from_polygon(shp, network_type = 'walk')
# G_walk = ox.graph_from_polygon(shp, custom_filter=cf)
# # CLAIRE: Not doing sidewalk here b/c for some reason was throwing errors
#
# print(len(G_orig), 'original')
# print(len(G_walk), 'custom filter')
#
# ax = ox.plot_graph(G_orig, edge_color = 'w', node_size = 0)
# ax = ox.plot_graph(G_walk, edge_color = 'w', node_size = 0)
