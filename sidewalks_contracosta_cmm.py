# Plotting various sidewalk filters for Contra Costa County, beginning with only Richmond
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
G = nx.compose(G_orig, G_walk)

ax = ox.plot_graph(G_orig, edge_color = 'r')
ox.plot_graph(G_sidewalk,ax = ax)

nodes = ox.graph_to_gdfs(G_orig, edges=False)
c = nodes.unary_union.centroid

fig,ax = ox.plot_graph(G_sidewalk, ax=ax, edge_color = 'black')
plt.show()

fig,ax = plt.subplots(1)
ox.plot_graph(G_walk,ax=ax,edge_color = 'green')

fig,ax = plt.subplots(1)
ox.plot_graph(G_orig,ax=ax,edge_color = 'r')


# Plot original walking edges in white, custom filter in yellow, sidewalk in green
# TODO: THIS PLOT
