# This code calculates driving distance matrices for "areas" (from shapefiles)
# rather than counties.

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

k_neighbors = 100 # Find this many nearest neighbors
max_distance = 4 # Find all neighbors within this number of miles
# Read in county boundaries
county_gdf = gpd.read_file(os.path.join("data","cb_2018_us_county_500k.zip"))
county_gdf = county_gdf[county_gdf["STATEFP"]=='06'] #Just california

ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4269'
wgs84 = 'EPSG:4326'

# Building candidate sites GeoDataFrame
# sites_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'candidate_sites_campuses.csv')
# sites_df_raw = pd.read_csv(sites_path)
# sites_df_raw = sites_df_raw.loc[sites_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]
# sites_geom = gpd.points_from_xy(sites_df_raw.LON, sites_df_raw.LAT, crs = nad83)
# sites_gdf = gpd.GeoDataFrame(sites_df_raw, geometry = sites_geom, crs = nad83)
sites_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'estimated_square_footages.csv')
sites_df_raw = pd.read_csv(sites_path)
sites_df_raw = sites_df_raw.loc[sites_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]
sites_geom = gpd.points_from_xy(sites_df_raw.LON, sites_df_raw.LAT, crs = nad83)
sites_gdf = gpd.GeoDataFrame(sites_df_raw, geometry = sites_geom, crs = nad83)
sites_gdf["id_site"] = np.arange(len(sites_gdf))

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

# Building Wilmington shapefile
wilmington_path = os.path.join(os.getcwd(), 'data', 'LA_Times_Neighborhood_Boundaries', 'LA_Times_Neighborhood_Boundaries.shp')
wilmington_gdf = gpd.read_file(wilmington_path)
wilmington_gdf['geometry'] = wilmington_gdf['geometry'].unary_union
del wilmington_gdf['OBJECTID']

# Building Richmond shapefiles
richmond_path = os.path.join(os.getcwd(), 'data', 'California_cities', 'Cities2015.shp')
richmond_gdf = gpd.read_file(richmond_path)
richmond_gdf = richmond_gdf.loc[richmond_gdf['NAME'] == "Richmond"].dissolve()
richmond_gdf['geometry'] = richmond_gdf['geometry'].unary_union

richmond_gdf = richmond_gdf.rename(columns={"NAME":"name"}).iloc[:, [1,0]]

# names of areas of interest
ca_areas = ['Wilmington']
#ca_areas = ['Richmond']

# dataset of area name, geometry column
gdf = wilmington_gdf
#gdf = richmond_gdf
gdf = gdf.to_crs(nad83)

area_graph_buffer = 0.1 # Add on this distance to get street nodes/edges from neighboring counties too.
# county = 'Contra Costa';county_fips = '013'
area = 'Wilmington'
#area = 'Richmond'

for area in ca_areas:
    output_area = area.lower().replace(' ', '')
    output_file_name = os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_walk_' + output_area + '.csv')
    if not(os.path.exists(output_file_name)): # If distance matrix has not been calculated yet
        # Get graph for area
        print("Getting graph for " + area)
        area_bbox = gdf.loc[gdf["name"]==area,'geometry'].unary_union
        if not(os.path.exists(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + output_area + '.graphml'))): # If graph has not been downloaded yet
            area_bbox_buffered = area_bbox.buffer(area_graph_buffer)
            area_graph = get_county_walk_graph_from_polygon(area_bbox_buffered, nad83)
            ox.save_graphml(area_graph, os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + output_area + '.graphml'))
        else: #Load graph from disk
            area_graph = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + output_area + '.graphml'))
            area_graph = ox.project_graph(area_graph, nad83)
        # Get the sites and block groups for just this area
        sites_area_gdf = sites_gdf.loc[sites_gdf.within(area_bbox)]
        bgs_area_gdf = bgs_pt_gdf.loc[bgs_pt_gdf.within(area_bbox)]

        # Get the "names" of the sites and block groups.
        name_index = {i:bgs_area_gdf.iloc[i]['GISJOIN'] for i in range(0, len(bgs_area_gdf))}
        name_columns = {i:sites_area_gdf.iloc[i]['id_site'] for i in range(0, len(sites_area_gdf))}

        # Initialize blank matrix
        dist_to_site_matrix = np.NaN*np.zeros((len(bgs_area_gdf), len(sites_area_gdf)))
        dist_to_site_df = pd.DataFrame(dist_to_site_matrix)
        dist_to_site_df.rename(index = name_index, columns = name_columns, inplace = True)

        # Calculate distance matrix loop
        print("Measuring distances for " + area)
        num_bgs = 0

        for _,bg_row in bgs_area_gdf.iterrows():
            # For timing purposes, see progress
            num_bgs += 1
            if num_bgs%10 == 0:
                print(num_bgs)
            # Get nearest node to blockgroup lat/long
            node_origin = get_coords_and_nearest_node(bg_row['GISJOIN'], 'GISJOIN', bgs_area_gdf, area_graph)

            # Find the nearest candidate sites
            sites_nearby = get_nearby_sites_lat_long(bg_row, sites_area_gdf, k_neighbors, max_distance)
            for site in sites_nearby: # For each site
                # Find the nearest node on the graph
                node_target = get_coords_and_nearest_node(site, 'id_site', sites_area_gdf, area_graph)
                try:
                    # Calculate travel distance
                    travel_dist_m = nx.shortest_path_length(area_graph, node_origin, node_target, weight = 'length')
                    # Set travel distance in distance matrix in miles
                    dist_to_site_df.loc[bg_row['GISJOIN'], site] = round(travel_dist_m/1609.344, 2)
                except:
                    dist_to_site_df.loc[bg_row['GISJOIN'], site] = None

# for _, bg_row in bgs_area_gdf.iterrows():
#     distances = calculate_haversine_distances(bg_row["LAT"],bg_row["LON"],
#                                           sites_area_gdf["LAT"].to_numpy(),sites_area_gdf["LON"].to_numpy())
#     print(distances)
#     if len(distances)>k_neighbors:
#         k_nearest_distance = np.partition(distances,k_neighbors)[k_neighbors]
#         print(k_nearest_distance)
#     else:
#         k_nearest_distance = np.max(distances)
# #     k_nearest_idx = distances<k_nearest_distance
# #     close_enough_idx = distances<max_distance
#     max_distance = max((k_nearest_distance,max_distance))
#     print(max_distance)
# #     k_nearest_idx = np.argpartition(distances,k)[:k].tolist()
# #     close_enough_idx = list(np.where(distances<max_distance)[0])
# #     print(type(close_enough_idx))
# #     print(np.unique(close_enough_idx+k_nearest_idx))
#     bg_nearest_sites = sites_area_gdf.loc[distances<max_distance,'id_site'].to_list()
#     print(bg_nearest_sites)

dist_to_site_df
dist_to_site_df.to_csv(output_file_name)
