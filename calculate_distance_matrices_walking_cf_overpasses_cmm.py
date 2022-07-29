# This script calculates distance matrices for counties in California using
# a custom filter that cuts out small paths/service roads and considers secondary
# roads and cuts out a 15m radius around overpasses out of the model.

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

import warnings

warnings.filterwarnings('ignore')

#CLAIRE: change distance matrix file to edited file
from distance_matrix_functions_cmm import *

k_neighbors = 10 # Find this many nearest neighbors
max_distance = 4 # Find all neighbors within this number of miles
# Read in county boundaries
county_gdf = gpd.read_file(os.path.join("data","cb_2018_us_county_500k.zip"))
county_gdf = county_gdf[county_gdf["STATEFP"]=='06'] #Just california

ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4269'
wgs84 = 'EPSG:4326'
projected = 'EPSG:32610' # for buffering

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

# # Building overpasses data
# overpass_buffer_meters = 75
# overpass_path = os.path.join(os.getcwd(), 'data', 'State_Highway_Bridges', 'State_Highway_Bridges.shp')
# overpass_gdf = gpd.read_file(overpass_path)
# overpass_gdf = gpd.GeoDataFrame(overpass_gdf, geometry=gpd.points_from_xy(overpass_gdf.LON, overpass_gdf.LAT), crs = nad83)
# buffers = overpass_gdf.to_crs(projected).geometry.buffer(overpass_buffer_meters)
# overpasses = buffers.to_crs(nad83).unary_union

# Building out highways buffer data
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

highways_buffer = highways.to_crs(projected).geometry.buffer(15) # 15 m buffer around highways
highways_buffer = highways_buffer.to_crs('EPSG:4326')
# highways are correct here
highways_buffer_union = highways_buffer.unary_union

# Getting county FIPS codes
ca_county_names = [ \
                    'Alameda', 'Alpine', 'Amador', 'Butte', 'Calaveras', 'Colusa', 'Contra Costa',
                   'Del Norte', 'El Dorado', 'Fresno', 'Glenn', 'Humboldt', 'Imperial', 'Inyo',
                   'Kern', 'Kings', 'Lake', 'Lassen', 'Los Angeles', 'Madera', 'Marin', 'Mariposa',
                   'Mendocino', 'Merced', 'Modoc', 'Mono', 'Monterey', 'Napa', 'Nevada', 'Orange',
                   'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
                   'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
                   'Santa Barbara', 'Santa Clara','Santa Cruz','Shasta', 'Sierra', 'Siskiyou',
                   'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
                   'Tuolumne','Ventura', 'Yolo', 'Yuba'
                   ]
ca_county_fips = ['00' + str(int(num)) for num in np.linspace(1, 115, 58)]
ca_county_fips = [num[-3:] for num in ca_county_fips]
ca_counties = {ca_county_names[i]:ca_county_fips[i] for i in range(len(ca_county_names))}
# Subset of counties to limit the analysis to just these counties.
ca_counties_subset = [ \
                        # 'Alameda', 'Alpine', 'Amador', 'Butte',
                        # 'Calaveras', 'Colusa',
                        'Contra Costa',
                        # 'Del Norte', 'El Dorado', 'Fresno', 'Glenn',
                        # 'Humboldt', 'Imperial', 'Inyo',
                        # 'Kern', 'Kings', 'Lake', 'Lassen',
                        # 'Los Angeles',
                        # 'Madera', 'Marin', 'Mariposa',
                        # 'Mendocino', 'Merced', 'Modoc', 'Mono',
                        # 'Monterey', 'Napa', 'Nevada', 'Orange',
                        # 'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
                        # 'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
                        # 'Santa Barbara', 'Santa Clara','Santa Cruz','Shasta', 'Sierra', 'Siskiyou',
                        # 'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
                        # 'Tuolumne','Ventura', 'Yolo', 'Yuba'
                        ]
ca_counties = {county: ca_counties[county] for county in ca_counties_subset}
county_graph_buffer = 0.1 # Add on this distance to get street nodes/edges from neighboring counties too.
county = 'Contra Costa';county_fips = '013'


for county, county_fips in ca_counties.items():
    output_county = county.lower().replace(' ', '')
    output_file_name = os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_walk_cf_overpasses_' + output_county + '.csv')
    if not(os.path.exists(output_file_name)): # If distance matrix has not been calculated yet
        # Get graph for county
        print("Getting graph for " + county)
        county_bbox = county_gdf.loc[county_gdf["COUNTYFP"]==county_fips,'geometry'].unary_union
        if not(os.path.exists(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf_overpasses_' + output_county + '.graphml'))): # If graph has not been downloaded yet
            county_bbox_buffered = county_bbox.buffer(county_graph_buffer)
            #county_bbox_buffered = county_bbox_buffered.difference(overpasses) # cut out overpasses

            motorway_cf = ('''["highway"]["area"!~"yes"]["access"!~"private"]
                    ["highway"~"motorway"]
                    ["service"!~"private"]{}''').format(ox.settings.default_access)
            graph_raw = ox.graph_from_polygon(county_bbox_buffered, custom_filter=motorway_cf, simplify = True) # extract graph of motorways only
            graph = ox.project_graph(graph_raw, to_crs = nad83)
            highways = ox.graph_to_gdfs(graph, nodes = False)
            highways_buffer = highways.to_crs(projected).geometry.buffer(15) # 15 m buffer around highways
            highways_buffer = highways_buffer.to_crs(nad83)
            highways_buffer = highways_buffer.unary_union
            county_bbox_buffered = county_bbox_buffered.difference(highways_buffer) # take out all highways from graph

            county_graph = get_county_walk_graph_from_polygon(county_bbox_buffered, nad83, cf = True)
            ox.save_graphml(county_graph, os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf_overpasses_' + output_county + '.graphml'))
        else: #Load graph from disk
            county_graph = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf_overpasses_' + output_county + '.graphml'))
        # Get the sites and block groups for just this county
        sites_county_gdf = sites_gdf.loc[sites_gdf.within(county_bbox)]
        bgs_county_gdf = bgs_pt_gdf[bgs_pt_gdf["COUNTYFP"]==county_fips]

        # Get the "names" of the sites and block groups.
        name_index = {i:bgs_county_gdf.iloc[i]['GISJOIN'] for i in range(0, len(bgs_county_gdf))}
        name_columns = {i:sites_county_gdf.iloc[i]['id_site'] for i in range(0, len(sites_county_gdf))}

        # Initialize blank matrix
        dist_to_site_matrix = np.NaN*np.zeros((len(bgs_county_gdf), len(sites_county_gdf)))
        dist_to_site_df = pd.DataFrame(dist_to_site_matrix)
        dist_to_site_df.rename(index = name_index, columns = name_columns, inplace = True)

        # Calculate distance matrix loop
        print("Measuring distances for " + county)
        num_bgs = 0

        for _,bg_row in bgs_county_gdf.iterrows():
            # For timing purposes, see progress
            num_bgs += 1
            if num_bgs%10 == 0:
                print(num_bgs)
            # Get nearest node to blockgroup lat/long
            node_origin = get_coords_and_nearest_node(bg_row['GISJOIN'], 'GISJOIN', bgs_county_gdf, county_graph)

            # Find the nearest candidate sites
            sites_nearby = get_nearby_sites_lat_long(bg_row, sites_county_gdf, k_neighbors, max_distance)
            for site in sites_nearby: # For each site
                # Find the nearest node on the graph
                node_target = get_coords_and_nearest_node(site, 'id_site', sites_county_gdf, county_graph)
                try:
                    # Calculate travel distance
                    travel_dist_m = nx.shortest_path_length(county_graph, node_origin, node_target, weight = 'length')
                    # Set travel distance in distance matrix in miles
                    dist_to_site_df.loc[bg_row['GISJOIN'], site] = round(travel_dist_m/1609.344, 2)
                except:
                    dist_to_site_df.loc[bg_row['GISJOIN'], site] = None


#len(county_graph.edges)

#walk_edited = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf_overpasses_' + 'contracosta' + '.graphml'))
bbox = ox.utils_geo.bbox_from_point((37.9327, -122.32577), dist=500)
ox.plot_graph(county_graph, node_size = 0, bbox = bbox)

#county_graph_gdf = ox.graph_to_gdfs(county_graph)


dist_to_site_df
dist_to_site_df.to_csv(output_file_name)


#gdf.to_file(filename='/Users/clairemorton/Documents/__PSE/overpasses_contracosta_30.shp', driver='ESRI Shapefile')
