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

import warnings

overpass_path = os.path.join(os.getcwd(), 'data', 'State_Highway_Bridges', 'State_Highway_Bridges.shp')
overpass_gdf = gpd.read_file(overpass_path)

# EXAMPLE OVERPASS WORK ON RICHMOND:
# Name: SOLANO AVENUE OC
# Lat: ‎37.94327
# Long: ‎-122.324085
overpass_gdf = overpass_gdf.loc[overpass_gdf['OBJECTID'] == 2747]
G = ox.graph_from_point((37.937009, -122.326022), dist = 250, network_type = 'walk')
ox.plot_graph(G)
ox.plot_graph(G_delete)

G.graph["crs"]
# Function to delete edges within "dist" meters of point given by latitude,
# longitude from the given graph, optionally grpahing before/after graphs,
# and return the projected version of the given graph, with edges deleted
def delete_edges(latitude, longitude, dist, graph, show_graph = False):
    graph_proj = ox.project_graph(graph)
    geom = gpd.points_from_xy([longitude], [latitude]) # create point
    gdf = gpd.GeoDataFrame(geometry = geom, crs = "nad83").to_crs(graph_proj.graph['crs']) # project to graph CRS
    i = 0
    ne, distance = ox.nearest_edges(graph_proj, X=gdf['geometry'].x, Y=gdf['geometry'].y, return_dist = True) # get nearest edge
    while(distance[0] < dist):
        graph_proj.remove_edge(u = ne[0][0], v = ne[0][1])
        ne, distance = ox.nearest_edges(graph_proj, X=gdf['geometry'].x, Y=gdf['geometry'].y, return_dist = True) # get nearest edge
        i = i+1
    print(i, "edges deleted")
    if(show_graph):
        fig, ax = ox.plot_graph(ox.project_graph(graph), edge_color = 'r', show=False, close=False)
        ax.scatter(gdf['geometry'].x, gdf['geometry'].y, c='b')
        ox.plot_graph(graph_proj, ax = ax, edge_color = 'y', show=False, close=False)
        plt.show()
    graph_proj = ox.project_graph(graph_proj, G.graph["crs"])
    return graph_proj

G_delete = delete_edges(37.937009, -122.326022, 160.934, G, True)

# DATASET OF ALL NOT DESIRED OVERPASSES IN RICHMOND
nad83 = 'EPSG:4269'
wgs84 = 'EPSG:4326'
projected = 'EPSG:3857'

overpass_path = os.path.join(os.getcwd(), 'data', 'State_Highway_Bridges', 'State_Highway_Bridges.shp')
overpass_gdf = gpd.read_file(overpass_path)
interstate_names = ['INTERSTATE 580', 'I 580 EB', 'I 580 WB','INTERSTATE ROUTE 580', 'I 580', 'STATE ROUTE 580']
overpass_richmond = overpass_gdf.loc[overpass_gdf['FAC'].isin(interstate_names) | overpass_gdf['INTERSEC'].isin(interstate_names)]
overpass_richmond_gdf = gpd.GeoDataFrame(overpass_richmond, geometry=gpd.points_from_xy(overpass_richmond.LON, overpass_richmond.LAT))

overpass_richmond_gdf
#overpass_richmond_gdf = overpass_richmond_gdf.to_crs(nad83)
# load Richmond data
# Building Richmond shapefiles
richmond_gdf.crs

area_graph_buffer = .1
richmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
richmond_gdf = gpd.read_file(richmond_path)
richmond_gdf = richmond_gdf.loc[richmond_gdf['NAME'] == "Richmond"].dissolve()
richmond_gdf['geometry'] = richmond_gdf['geometry'].unary_union

richmond_gdf = richmond_gdf.rename(columns={"NAME":"name"}).iloc[:, [1,0]]
# richmond_gdf = richmond_gdf.to_crs(projected) #transform from nad83 (4269) to 3857 
# (commented because the units get changed)
richmond_gdf['geometry'] = richmond_gdf.buffer(area_graph_buffer)
richmond_gdf = richmond_gdf.to_crs(nad83) #transform back

richmond_gdf['geometry'].unary_union

overpass_richmond_gdf['in_richmond'] = overpass_richmond_gdf.within(richmond_gdf.unary_union)
in_richmond = overpass_richmond_gdf.loc[overpass_richmond_gdf['in_richmond']==True]

# intersect Richmond with overpass data

# DATASET OF ALL NOT DESIRED OVERPASSES IN WILMINGTON
