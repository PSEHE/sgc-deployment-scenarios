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

warnings.filterwarnings('ignore')

### MAP GEODATAFRAME ON OPENSTREETMAP BASEMAP

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

### GET GRAPH FOR DESIRED LOCATION

def get_county_drive_graph(in_county, in_crs):
    
    county = in_county + ', California, USA'
    graph_raw = ox.graph_from_place(county, network_type = 'drive', simplify = True)

    graph = ox.project_graph(graph_raw, to_crs = in_crs)
    graph = ox.speed.add_edge_speeds(graph)
    graph = ox.speed.add_edge_travel_times(graph)

    county_nodes_gdf, county_edges_gdf = ox.graph_to_gdfs(graph, nodes = True, edges = True)

    county_edges_gdf_reset = county_edges_gdf.reset_index()
    county_edges_gdf_reset.rename(columns = {'u':'from_node', 'v':'to_node'}, inplace = True)
    
    return(graph, county_nodes_gdf, county_edges_gdf_reset)

### RESTRICT SITES AND BLOCKGROUPS TO COUNTY OF INTEREST

def make_county_bbox(in_nodes_gdf):
    
    lon_max = in_nodes_gdf['lon'].max()
    lon_min = in_nodes_gdf['lon'].min()
    lon_avg = (lon_max + lon_min)/2

    lat_max = in_nodes_gdf['lat'].max()
    lat_min = in_nodes_gdf['lat'].min()
    lat_avg = (lat_min + lat_max)/2

    county_bbox_coords = [(lon_min, lat_min), (lon_min, lat_max), (lon_max, lat_max), (lon_max, lat_min)]
    county_bbox = shapely.geometry.Polygon(county_bbox_coords)
    
    return(county_bbox)

def clip_sites_to_county(in_county_bbox, in_sites_gdf):
    
    sites_county_gdf = in_sites_gdf[in_sites_gdf.within(in_county_bbox)]
    
    return(sites_county_gdf)


def clip_bgs_to_county(in_county_bbox, in_bgs_pt_gdf, in_county_fips):
    
    bgs_county_gdf = in_bgs_pt_gdf[in_bgs_pt_gdf.within(in_county_bbox)].reset_index(drop = True)
    bgs_county_gdf['CNTY_FIPS'] = bgs_county_gdf['GISJOIN'].str[4:7]
    bgs_county_gdf = bgs_county_gdf.loc[bgs_county_gdf['CNTY_FIPS'] == in_county_fips]
    
    return(bgs_county_gdf)

def buffer_bgs(in_bgs_pt_gdf_bbox, in_crs):
    bgs_pt_gdf_bbox_proj = in_bgs_pt_gdf_bbox.to_crs('NAD_1983_California_Teale_Albers_FtUS')

    one_mile = 5280
    bgs_buffer = bgs_pt_gdf_bbox_proj.buffer(one_mile*3)

    bgs_county_buffer_gdf = gpd.GeoDataFrame(in_bgs_pt_gdf_bbox['GISJOIN'])
    bgs_county_buffer_gdf['geometry'] = bgs_buffer

    bgs_county_buffer_gdf = bgs_county_buffer_gdf.to_crs(in_crs)
    
    return(bgs_county_buffer_gdf)

### GET DISTANCE FROM BLOCKGROUP TO SITES

def get_coords_and_nearest_node(in_pt, in_colname, in_pt_gdf, in_graph):

    pt_geom = in_pt_gdf.loc[in_pt_gdf[in_colname] == in_pt]

    latitude = mean(pt_geom.LAT) #Edge case: a small handful of sites have two sets of coords 
    longitude = mean(pt_geom.LON)

    pt_coords = [float(latitude), float(longitude)]
    pt_nearest_node = ox.get_nearest_node(in_graph, pt_coords, method = 'euclidean')

    return(pt_nearest_node)

def get_nearby_sites(in_bg, in_bg_buffers, in_sites):

    bg_buffer = in_bg_buffers.loc[in_bg_buffers['GISJOIN'] == in_bg, 'geometry'].reset_index(drop = True)[0]
    bg_nearest_sites = in_sites[in_sites.within(bg_buffer)]['id_site']

    return(bg_nearest_sites)

def get_steps_in_route(in_route):

    steps_in_route = []

    for i in range(0, len(in_route)):
        steps_in_route.append([in_route[i-1], in_route[i]])

    steps_in_route = steps_in_route[1:]

    return(steps_in_route)

def get_travel_time(in_steps, in_edges):

    travel_times_sec = []

    for step in range(0, len(in_steps)):

        step_in_route = in_steps[step]
        step_duration_sec = in_edges.loc[(in_edges['from_node'] == step_in_route[0]) & (in_edges['to_node'] == step_in_route[1])]['travel_time']
        travel_times_sec.append(step_duration_sec)

    travel_times_min = [float(travel_time)/60 for travel_time in travel_times_sec]
    travel_time_min = round(sum(travel_times_min), 2)

    return(travel_time_min)


