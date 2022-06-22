# This code is an example of taking a point close to an edge/node, finding what
# edge/node it is closest to, and deleting that edge/node.

# Import packages
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

import warnings

# Create simple example graph
G_raw = ox.graph_from_bbox(37.79, 37.785, -122.41, -122.415, network_type='drive', simplify = True)
G = ox.project_graph(G_raw, to_crs = "nad83")

#G_projected = ox.project_graph(G)
ox.plot_graph(G)

#### ---------------------Delete a single edge ---------------------------------
# Create point, from which we will delete closest edge
latitude = 37.787
longitude = -122.412

G_proj = ox.project_graph(G)
geom = gpd.points_from_xy([longitude], [latitude]) # create point
gdf = gpd.GeoDataFrame(geometry = geom, crs = "nad83").to_crs(G_proj.graph['crs']) # project to graph CRS

ne = ox.nearest_edges(G_proj, X=gdf['geometry'].x, Y=gdf['geometry'].y) # get nearest edge
ec = ['b' if (u==ne[0][0] and v==ne[0][1]) else 'r' for u, v, k in G.edges(keys=True)]
fig, ax = ox.plot_graph(G_proj, edge_color=ec, edge_linewidth = 3, show=False, close=False)
ax.scatter(gdf['geometry'].x, gdf['geometry'].y, c='b')
plt.show()

# Delete closest edge
G_proj.remove_edge(u = ne[0][0], v = ne[0][1])
fig, ax = ox.plot_graph(G_proj, edge_color='r', edge_linewidth = 3, show=False, close=False)
ax.scatter(gdf['geometry'].x, gdf['geometry'].y, c='b')
plt.show()


#### ---------------------Delete a single node ---------------------------------
# Create point, from which we will delete closest node
latitude = 37.787
longitude = -122.412

G_proj = ox.project_graph(G)
geom = gpd.points_from_xy([longitude], [latitude]) # create point
gdf = gpd.GeoDataFrame(geometry = geom, crs = "nad83").to_crs(G_proj.graph['crs']) # project to graph CRS

nn = ox.nearest_nodes(G_proj, X=gdf['geometry'].x, Y=gdf['geometry'].y) # get nearest edge
nc = ['b' if (i==nn[0]) else 'r' for i in G.nodes()]
fig, ax = ox.plot_graph(G_proj, node_color=nc, node_size = 30, show=False, close=False)
ax.scatter(gdf['geometry'].x, gdf['geometry'].y, c='b')
plt.show()

# Delete closest node
G_proj.remove_node(nn[0])
fig, ax = ox.plot_graph(G_proj, node_color='r', node_size = 30, show=False, close=False)
ax.scatter(gdf['geometry'].x, gdf['geometry'].y, c='b')
plt.show()
