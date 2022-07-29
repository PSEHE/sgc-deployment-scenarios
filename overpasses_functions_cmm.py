# Note that walking graph without overpasses + with custom filter has already been created
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

from distance_matrix_functions_cmm import *
from shapely import validation

nad83 = 'EPSG:4269'
wgs84 = 'EPSG:4326'
#projected = 'EPSG:3857'
projected = 'EPSG:32610'

# Contra Costa Buffer
county_gdf = gpd.read_file(os.path.join("data","cb_2018_us_county_500k.zip"))
county_gdf = county_gdf[county_gdf["STATEFP"]=='06'] #Just california
county_graph_buffer = 0.1 # Add on this distance to get street nodes/edges from neighboring counties too.
county = 'Contra Costa';county_fips = '013'
county_bbox = county_gdf.loc[county_gdf["COUNTYFP"]==county_fips,'geometry'].to_crs('EPSG:4326').unary_union
county_bbox_buffered = county_bbox.buffer(county_graph_buffer)

# Extract motorways
motorway_cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
        ["highway"~"motorway"]["highway"!~"motorway_link"]
        ["service"!~"private"]{}''').format(ox.settings.default_access)
graph_raw = ox.graph_from_polygon(county_bbox_buffered, custom_filter=motorway_cf, simplify = True) # extract graph of motorways only
graph = ox.project_graph(graph_raw, to_crs = nad83)
highways = ox.graph_to_gdfs(graph, nodes = False)

highways_buffer = highways.to_crs(projected).geometry.buffer(15) # 15 m buffer around highways
highways_buffer = highways_buffer.to_crs('EPSG:4326')

# highways are correct here
highways_buffer_union = highways_buffer.unary_union

#shapely.geometry.Polygon(highways_buffer_union.exterior)
county_bbox_buffered2 = county_bbox_buffered.difference(highways_buffer_union) # take out all highways from graph

# plot shows the interior polygon that is fully formed from holes and makes the code not work later
for geom in county_bbox_buffered2.geoms:
    plt.plot(*geom.exterior.xy)
list(county_bbox_buffered2.geoms)

# Set (current) axis to be equal before showing plot
plt.gca().axis("equal")
plt.show()

# This polygon ends up not being valid, but otherwise I think it would work
county_bbox_buffered3 = shapely.geometry.Polygon(county_bbox_buffered.exterior.coords, [inner.exterior.coords for inner in highways_buffer])
county_bbox_buffered3
shapely.validation.explain_validity(county_bbox_buffered3)

# Shows the exterior problem -- gets rid of an interior highway, and (when joined to the county) gets rid of the middle section
highways_buffer_union.exterior
shapely.geometry.Polygon(county_bbox_buffered.exterior.coords, [highways_buffer_union.exterior.coords])

# trying to make a valid polygon
valid_county_bbox_buffered = shapely.validation.make_valid(county_bbox_buffered3)
type(valid_county_bbox_buffered)
# polygon is so long that creating graph from it takes an extremely long time
len(valid_county_bbox_buffered)


cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
        ["highway"~"pedestrian|living_street|tertiary|secondary|primary|residential"]
        ["service"!~"private"]{}''').format(ox.settings.default_access)
graph = get_county_walk_graph_from_polygon(valid_county_bbox_buffered, nad83, cf = True, simplify = False) # do not simplify when intersecting with highways (so that overpasses do get taken out)
graph_s=ox.simplification.simplify_graph(graph)

# Graphs to check whether overpasses were successfully taken out
bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=2000)
ox.plot_graph(graph, node_size = 0, bbox = bbox)

bbox = ox.utils_geo.bbox_from_point((37.92355, -122.36079), dist=2000)
ox.plot_graph(graph, node_size = 0, bbox = bbox)

# SECTION ON TAKING OUT RICHMOND OVERPASSES ONLY
richmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
richmond_gdf = gpd.read_file(richmond_path)
richmond_gdf = richmond_gdf.loc[richmond_gdf['NAME'] == "Richmond"].dissolve()
richmond_gdf['geometry'] = richmond_gdf['geometry'].unary_union

motorway_cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
        ["highway"~"motorway"]["highway"!~"motorway_link"]
        ["service"!~"private"]{}''').format(ox.settings.default_access)
richmond_gdf = richmond_gdf.rename(columns={"NAME":"name"}).iloc[:, [1,0]]
richmond_gdf = richmond_gdf.to_crs('EPSG:4326')
richmond = richmond_gdf.unary_union
richmond = richmond.buffer(county_graph_buffer)

graph_raw = ox.graph_from_polygon(richmond, custom_filter=motorway_cf, simplify = False) # extract graph of motorways only
graph = ox.project_graph(graph_raw, to_crs = nad83)
highways = ox.graph_to_gdfs(graph, nodes = False)

highways_buffer = highways.to_crs(projected).geometry.buffer(30) # 15 m buffer around highways
highways_buffer = highways_buffer.to_crs('EPSG:4326')
# highways are correct here
highways_buffer_union = highways_buffer.unary_union

difference = county_bbox_buffered.difference(highways_buffer_union) # take out all highways from graph
cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
        ["highway"~"pedestrian|living_street|tertiary|secondary|primary|residential"]
        ["service"!~"private"]{}''').format(ox.settings.default_access)
graph = get_county_walk_graph_from_polygon(difference, nad83, cf = True, simplify = False) # do not simplify when intersecting with highways (so that overpasses do get taken out)
graph_s=ox.simplification.simplify_graph(graph)

# Graphs to check whether overpasses were successfully taken out
bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=2000)
ox.plot_graph(graph, node_size = 0, bbox = bbox)

bbox = ox.utils_geo.bbox_from_point((37.92355, -122.36079), dist=2000)
ox.plot_graph(graph, node_size = 0, bbox = bbox)
## EXTRA CODE/DEPRECATED
# overpass_path = os.path.join(os.getcwd(), 'data', 'State_Highway_Bridges', 'State_Highway_Bridges.shp')
# overpass_gdf = gpd.read_file(overpass_path)
#
# # EXAMPLE OVERPASS WORK ON RICHMOND:
# # Name: SOLANO AVENUE OC
# # Lat: ‎37.94327
# # Long: ‎-122.324085
# overpass_gdf = overpass_gdf.loc[overpass_gdf['OBJECTID'] == 2747]
# G = ox.graph_from_point((37.937009, -122.326022), dist = 250, network_type = 'walk')
#
# G.graph["crs"]
# # Function to delete edges within "dist" meters of point given by latitude,
# # longitude from the given graph, optionally grpahing before/after graphs,
# # and return the projected version of the given graph, with edges deleted
# def delete_edges(latitude, longitude, dist, graph, show_graph = False):
#     graph_proj = ox.project_graph(graph)
#     geom = gpd.points_from_xy([longitude], [latitude]) # create point
#     gdf = gpd.GeoDataFrame(geometry = geom, crs = "nad83").to_crs(graph_proj.graph['crs']) # project to graph CRS
#     i = 0
#     ne, distance = ox.nearest_edges(graph_proj, X=gdf['geometry'].x, Y=gdf['geometry'].y, return_dist = True) # get nearest edge
#     while(distance[0] < dist):
#         graph_proj.remove_edge(u = ne[0][0], v = ne[0][1])
#         ne, distance = ox.nearest_edges(graph_proj, X=gdf['geometry'].x, Y=gdf['geometry'].y, return_dist = True) # get nearest edge
#         i = i+1
#     print(i, "edges deleted")
#     if(show_graph):
#         fig, ax = ox.plot_graph(ox.project_graph(graph), edge_color = 'r', show=False, close=False)
#         ax.scatter(gdf['geometry'].x, gdf['geometry'].y, c='b')
#         ox.plot_graph(graph_proj, ax = ax, edge_color = 'y', show=False, close=False)
#         plt.show()
#     graph_proj = ox.project_graph(graph_proj, G.graph["crs"])
#     return graph_proj
#
# G_delete = delete_edges(37.937009, -122.326022, 15, G, True)
#
# # DATASET OF ALL NOT DESIRED OVERPASSES IN RICHMOND
# nad83 = 'EPSG:4269'
# wgs84 = 'EPSG:4326'
# #projected = 'EPSG:3857'
# projected = 'EPSG:32610'
#
# overpass_path = os.path.join(os.getcwd(), 'data', 'State_Highway_Bridges', 'State_Highway_Bridges.shp')
# overpass_gdf = gpd.read_file(overpass_path)
#
# overpass_gdf = gpd.GeoDataFrame(overpass_gdf, geometry=gpd.points_from_xy(overpass_gdf.LON, overpass_gdf.LAT), crs = nad83)
# #overpass_gdf = overpass
# #buffers = overpass_gdf.to_crs(projected).geometry.buffer(15)
# #buffers.unary_union
#
# interstate_names = ['INTERSTATE 580', 'I 580 EB', 'I 580 WB','INTERSTATE ROUTE 580', 'I 580', 'STATE ROUTE 580']
# overpass_richmond = overpass_gdf.loc[overpass_gdf['FAC'].isin(interstate_names) | overpass_gdf['INTERSEC'].isin(interstate_names)]
# overpass_richmond_gdf = gpd.GeoDataFrame(overpass_richmond, geometry=gpd.points_from_xy(overpass_richmond.LON, overpass_richmond.LAT),crs= 'EPSG:4269')
#
# buffers = overpass_richmond_gdf.to_crs(projected).geometry.buffer(15)
# overpasses = buffers.to_crs(nad83).unary_union
#
#
# # Building Richmond shapefiles
# richmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
# richmond_gdf = gpd.read_file(richmond_path)
# richmond_gdf = richmond_gdf.loc[richmond_gdf['NAME'] == "Richmond"].dissolve()
# richmond_gdf['geometry'] = richmond_gdf['geometry'].unary_union
#
# richmond_gdf = richmond_gdf.rename(columns={"NAME":"name"}).iloc[:, [1,0]]
# richmond = richmond_gdf.unary_union
#
# richmond_gdf.crs
# buffers.crs
#
# richmond.difference(overpasses)
#
# # Trying the graph extraction method to get highways and then buffer them to make a shapefilesrichmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
# richmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
# richmond_gdf = gpd.read_file(richmond_path)
# richmond_gdf = richmond_gdf.loc[richmond_gdf['NAME'] == "Richmond"].dissolve()
# richmond_gdf['geometry'] = richmond_gdf['geometry'].unary_union
#
# richmond_gdf = richmond_gdf.rename(columns={"NAME":"name"}).iloc[:, [1,0]]
# richmond = richmond_gdf.unary_union
#
# nad83 = 'EPSG:4269'
# in_crs = nad83
# projected = 'EPSG:32610'
# motorway_cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
#         ["highway"~"motorway"]
#         ["service"!~"private"]{}''').format(ox.settings.default_access)
# graph_raw = ox.graph_from_polygon(richmond, custom_filter=motorway_cf, simplify = True)
# graph = ox.project_graph(graph_raw, to_crs = in_crs)
# #ox.plot_graph(graph)
# highways = ox.graph_to_gdfs(graph, nodes = False)
# buffer = highways.to_crs(projected).geometry.buffer(15)
# buffer = buffer.unary_union
# buffer
#
# bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=500)
# #bbox.crs
# nad83 = 'EPSG:4269'
# in_crs = nad83
# projected = 'EPSG:32610'
# motorway_cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
#         ["highway"~"motorway"]
#         ["service"!~"private"]{}''').format(ox.settings.default_access)
# graph_raw = ox.graph_from_bbox(bbox[0], bbox[1], bbox[2], bbox[3], custom_filter=motorway_cf, simplify = True)
# #ox.plot_graph(graph_raw)
# graph = ox.project_graph(graph_raw, to_crs = in_crs)
# #highways = ox.graph_to_gdfs(graph, nodes = False)
# buffer = highways.to_crs(projected).geometry.buffer(15)
# buffer = buffer.to_crs('epsg:4326')
# buffer = buffer.unary_union
#
# buffer.centroid.xy
#
# from shapely.geometry import box
# bbox_poly = box(bbox[0], bbox[1], bbox[2], bbox[3])
# bbox_poly = bbox_poly.unary_union
# #bbox_poly = gpd.GeoDataFrame(geometry = bbox_poly)
# #bbox_poly_gdf = gpd.GeoDataFrame({'Name': [2]}, geometry=bbox_poly)
# bbox_poly.difference(buffer)
# graph = ox.graph_from_bbox()






#multiline = shapely.geometry.MultiLineString(list(highways['geometry']))
#merged_multiline = shapely.ops.linemerge(multiline)

#highways_buffer = merged_multiline.to_crs(projected).geometry.buffer(15)
#
# highways_buffer = highways.to_crs(projected).geometry.buffer(25) # 15 m buffer around highways
# highways_buffer = highways_buffer.to_crs(nad83)
# highways_buffer_union = highways_buffer.unary_union
# county_bbox_buffered = county_bbox_buffered.difference(highways_buffer_union) # take out all highways from graph
#
# county_graph = get_county_walk_graph_from_polygon(county_bbox_buffered, nad83, cf = True)
#
# bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=2000)
# ox.plot_graph(county_graph, node_size = 0, bbox = bbox)
#
#
# # section where I just try to get overpasses in this region taken out of the graph
# bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=2000)
# graph_raw_bbox = ox.graph_from_bbox(bbox[0], bbox[1], bbox[2], bbox[3], custom_filter=motorway_cf, simplify = True) # extract graph of motorways only
# graph = ox.project_graph(graph_raw_bbox, to_crs = nad83)
# highways = ox.graph_to_gdfs(graph, nodes = False)
#
# highways_buffer = highways.to_crs(projected).geometry.buffer(25) # 15 m buffer around highways
# highways_buffer = highways_buffer.to_crs(nad83)
# #highways_buffer = highways_buffer.to_crs('EPSG:4326')
# highways_buffer_union = shapely.ops.unary_union(highways_buffer)
#
# big_buffer = highways.to_crs(projected).geometry.buffer(1000) # 15 m buffer around highways
# big_buffer = big_buffer.to_crs(nad83)
# #big_buffer = big_buffer.to_crs('EPSG:4326')
# big_buffer_union = shapely.ops.unary_union(big_buffer)
#
# difference = big_buffer_union.difference(highways_buffer_union)
#
#
#
#
# # Try to figure out how to make the polygon just outer and inner
# p = shapely.geometry.Polygon(big_buffer_union.exterior.coords, [highways_buffer_union.exterior.coords])
#
# # graph difference on larger plot
# # Plot each polygon shape directly
# for geom in difference.geoms:
#     plt.plot(*geom.exterior.xy)
# list(difference.geoms)[0]
#
# # Set (current) axis to be equal before showing plot
# plt.gca().axis("equal")
# plt.show()
#
# # graph highways buffer union on a larger plot
# plt.plot(*highways_buffer_union.exterior.xy)
# plt.gca().axis("equal")
# plt.show()
#
#
# #county_graph = get_county_walk_graph_from_polygon(difference, nad83, cf = True)
# #county_graph = get_county_walk_graph_from_polygon(p, nad83, cf = True)
# #ounty_graph = get_county_walk_graph_from_polygon(big_buffer_union, nad83, cf = True)
# cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
#         ["highway"~"pedestrian|living_street|tertiary|secondary|primary|residential"]
#         ["service"!~"private"]{}''').format(ox.settings.default_access)
# graph_over = ox.graph_from_polygon(difference, network_type = 'walk', custom_filter = cf, simplify = False)
# graph_raw = ox.graph_from_polygon(polygon, network_type = 'walk', custom_filter = cf, simplify = True)
# graph_over_s=ox.simplification.simplify_graph(graph_over)
#
# bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=2000)
# ox.plot_graph(graph_over_s, node_size = 0, bbox = bbox)
#
# ox.plot_graph(county_graph, node_size = 0, bbox = bbox)
# ox.plot_graph(ounty_graph, node_size = 0, bbox = bbox)
#overpass_richmond_gdf = overpass_richmond_gdf.to_crs(nad83)
# load Richmond data
# Building Richmond shapefiles

# area_graph_buffer = .1
# richmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
# richmond_gdf = gpd.read_file(richmond_path)
# richmond_gdf = richmond_gdf.loc[richmond_gdf['NAME'] == "Richmond"].dissolve()
# richmond_gdf['geometry'] = richmond_gdf['geometry'].unary_union
#
# richmond_gdf = richmond_gdf.rename(columns={"NAME":"name"}).iloc[:, [1,0]]
# # richmond_gdf = richmond_gdf.to_crs(projected) #transform from nad83 (4269) to 3857
# # (commented because the units get changed)
# richmond_gdf['geometry'] = richmond_gdf.buffer(area_graph_buffer)
# richmond_gdf = richmond_gdf.to_crs(nad83) #transform back
#
# # intersect Richmond with overpass data
# overpass_richmond_gdf['in_richmond'] = overpass_richmond_gdf.within(richmond_gdf.unary_union)
#
# in_richmond = overpass_richmond_gdf.loc[overpass_richmond_gdf['in_richmond']==True]
# in_richmond = in_richmond[['LAT', 'LON', 'NAME', 'FAC', 'INTERSEC']]
#
# # load Richmond walking graph and filter out all overpasses with 15 m buffer
# # load graph
#
# area = 'richmond'
# graph = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + area + '.graphml'))
# graph_deleted = graph
#
# head_in_richmond = in_richmond.iloc[[5, 6]]
# for index, overpass in head_in_richmond.iterrows():
#     graph_deleted = delete_edges(overpass['LAT'], overpass['LON'], 15, graph_deleted, False)
#
# function that takes a graph and dataset with 'LAT' and 'LON' columns, and
# takes out all edges of the graph within 'buffer' meters of all 'LAT' 'LON'
# points, and returns the edited graph
#def take_out_overpasses(graph, overpasses, buffer)


# DATASET OF ALL NOT DESIRED OVERPASSES IN WILMINGTON
