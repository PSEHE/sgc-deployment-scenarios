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

## ------------------------------ RICHMOND -------------------------------------
# Trying out different filters for sidewalk data
place = 'Richmond, California'

cf= ('''["area"!~"yes"]["highway"~"footway|pedestrian|path|steps|living_street|
        tertiary|residential|service"]["foot"!~"no"]["service"!~"private"]{}''')\
    .format(ox.settings.default_access)
cf_sidewalk=('["footway"~"sidewalk"]{}').format(ox.settings.default_access)
G_orig = ox.graph_from_place(place, network_type = "walk")
G_walk = ox.graph_from_place(place, custom_filter=cf)
G_sidewalk = ox.graph_from_place(place, custom_filter=cf_sidewalk)
print(len(G_orig), 'original')
print(len(G_walk), 'custom filter')
print(len(G_sidewalk), 'sidewalk')

ax = ox.plot_graph(G_orig, edge_color = 'w', node_size = 0)
ax = ox.plot_graph(G_walk, edge_color = 'w', node_size = 0)
ax = ox.plot_graph(G_sidewalk, edge_color = 'w', node_size = 0)

## --------------------------- WILMINGTON --------------------------------------
# Trying out different filters for sidewalk data
wilmington_path = os.path.join(os.getcwd(), 'data', 'LA_Times_Neighborhood_Boundaries', 'LA_Times_Neighborhood_Boundaries.shp')
wilmington_gdf = gpd.read_file(wilmington_path)
shp = wilmington_gdf['geometry'].unary_union
shp
cf= ('''["area"!~"yes"]["highway"~"footway|pedestrian|path|steps|living_street|
        tertiary|residential|service"]["foot"!~"no"]["service"!~"private"]{}''')\
    .format(ox.settings.default_access)
cf_sidewalk=('["footway"~"sidewalk"]{}').format(ox.settings.default_access)
G_orig = ox.graph_from_polygon(shp, network_type = 'walk')
G_walk = ox.graph_from_polygon(shp, custom_filter=cf)
# CLAIRE: Not doing sidewalk here b/c for some reason was throwing errors

print(len(G_orig), 'original')
print(len(G_walk), 'custom filter')

ax = ox.plot_graph(G_orig, edge_color = 'w', node_size = 0)
ax = ox.plot_graph(G_walk, edge_color = 'w', node_size = 0)
