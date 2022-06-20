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

from distance_matrix_functions import *

k_neighbors = 10
max_distance = 4
# %% markdown
# ## Build Distance Matrix
# %% markdown
# ### Read in requisite data and define CRS
# %% codecell
# Read in county boundaries
county_gdf = gpd.read_file(os.path.join("data","cb_2018_us_county_500k.zip"))
county_gdf = county_gdf[county_gdf["STATEFP"]=='06']
# %% codecell
ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4629'
wgs84 = 'EPSG:4326'

# %% codecell

# graph_california = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_California.graphml'))
# california_nodes_gdf = ox.graph_to_gdfs(graph_california, nodes = True, edges = False)

# %% codecell
sites_path = os.path.join(os.getcwd(), 'data', 'candidate_site_campuses_2021-11-17', 'candidate_sites_campuses.csv')

sites_df_raw = pd.read_csv(sites_path)
sites_df_raw = sites_df_raw.loc[sites_df_raw['cat_site'] != 'X', ['id_site', 'cat_site', 'SQFT_ROOF', 'LON', 'LAT']]

sites_geom = gpd.points_from_xy(sites_df_raw.LON, sites_df_raw.LAT, crs = nad83)
sites_gdf = gpd.GeoDataFrame(sites_df_raw, geometry = sites_geom, crs = nad83)
# %% codecell
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
# %% markdown
# ### Iterate through each county and build matrix
# %% codecell
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
# %% codecell

ca_counties_subset = [ \
                        # 'Alameda', 'Alpine', 'Amador', 'Butte',
                        # 'Calaveras', 'Colusa', 'Contra Costa',
                        # 'Del Norte', 'El Dorado', 'Fresno', 'Glenn',
                        # 'Humboldt', 'Imperial', 'Inyo',
                        # 'Kern', 'Kings', 'Lake', 'Lassen', 'Los Angeles',
                        'Madera', 'Marin', 'Mariposa',
                        # 'Mendocino', 'Merced', 'Modoc', 'Mono',
                        # 'Monterey', 'Napa', 'Nevada', 'Orange',
                        # 'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
                        # 'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
                        # 'Santa Barbara', 'Santa Clara','Santa Cruz','Shasta', 'Sierra', 'Siskiyou',
                        # 'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
                        # 'Tuolumne','Ventura', 'Yolo', 'Yuba'
                        ]

ca_counties = {county: ca_counties[county] for county in ca_counties_subset}

county_graph_buffer = 0.1
county = 'Santa Cruz';county_fips = '087'

for county, county_fips in ca_counties.items():
    output_county = county.lower().replace(' ', '')
    output_file_name = os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_' + output_county + '.csv')
    if not(os.path.exists(output_file_name)):
    # county = 'Los Angeles';county_fips = '037'
        # Get graph for county
        print("Getting graph for " + county)
        county_bbox = county_gdf.loc[county_gdf["COUNTYFP"]==county_fips,'geometry'].unary_union
        if not(os.path.exists(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_' + output_county + '.graphml'))):
            county_bbox_buffered = county_bbox.buffer(county_graph_buffer)
            county_graph = get_county_drive_graph_from_polygon(county_bbox_buffered, nad83)
            ox.save_graphml(county_graph, os.path.join(os.getcwd(), 'data', 'graphs', 'graph_' + output_county + '.graphml'))
        else:
            county_graph = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_' + output_county + '.graphml'))
        sites_county_gdf = sites_gdf.loc[sites_gdf.within(county_bbox)]
        bgs_county_gdf = bgs_pt_gdf[bgs_pt_gdf["COUNTYFP"]==county_fips]

        name_index = {i:bgs_county_gdf.iloc[i]['GISJOIN'] for i in range(0, len(bgs_county_gdf))}
        name_columns = {i:sites_county_gdf.iloc[i]['id_site'] for i in range(0, len(sites_county_gdf))}

        # Initialize blank matrix
        dist_to_site_matrix = np.NaN*np.zeros((len(bgs_county_gdf), len(sites_county_gdf)))
        dist_to_site_df = pd.DataFrame(dist_to_site_matrix)

        dist_to_site_df.rename(index = name_index, columns = name_columns, inplace = True)

        # Build matrix
        print("Measuring distances for " + county)
        num_bgs = 0
        for _,bg_row in bgs_county_gdf.iterrows():
            num_bgs += 1
            if num_bgs%10 == 0:
                print(num_bgs)
            node_origin = get_coords_and_nearest_node(bg_row['GISJOIN'], 'GISJOIN', bgs_county_gdf, county_graph)
            # node_origin = get_coords_and_nearest_node(bg_row['GISJOIN'], 'GISJOIN', bgs_county_gdf, graph_california)

            sites_nearby = get_nearby_sites_lat_long(bg_row, sites_county_gdf, k_neighbors, max_distance)

            for site in sites_nearby:

                node_target = get_coords_and_nearest_node(site, 'id_site', sites_county_gdf, county_graph)
                # node_target = get_coords_and_nearest_node(site, 'id_site', sites_county_gdf, graph_california)

                try:
                    travel_dist_m = nx.shortest_path_length(county_graph, node_origin, node_target, weight = 'length')
                    # travel_dist_m = nx.shortest_path_length(graph_california, node_origin, node_target, weight = 'length')

                    dist_to_site_df.loc[bg_row['GISJOIN'], site] = round(travel_dist_m/1609.344, 2)

                except:
                    dist_to_site_df.loc[bg_row['GISJOIN'], site] = None

        # #Write output to csv
        dist_to_site_df.to_csv(output_file_name)
        # %% codecell





































# for county, county_fips in ca_counties.items():
#     output_county = county.lower().replace(' ', '')
#     output_file_name = os.path.join(os.getcwd(), 'data', 'distance_matrices', 'distmatrix_' + output_county + '.csv')
#     if not(os.path.exists(output_file_name)):
#     # county = 'Los Angeles';county_fips = '037'
#     # county = 'Santa Cruz';county_fips = '087'
#     # Get graph for county
#         # print("Getting graph for " + county)
#         # county_graph, county_nodes_gdf, county_edges_gdf = get_county_drive_graph(county, nad83)
#         # ox.save_graphml(county_graph, os.path.join(os.getcwd(), 'data', 'graphs', 'graph_' + output_county + '.graphml'))
#         county_bbox = county_gdf.loc[county_gdf["COUNTYFP"]==county_fips,'geometry'].unary_union
#         sites_county_gdf = sites_gdf.loc[sites_gdf.within(county_bbox)]
#         bgs_county_gdf = bgs_pt_gdf[bgs_pt_gdf["COUNTYFP"]==county_fips]
#
#         name_index = {i:bgs_county_gdf.iloc[i]['GISJOIN'] for i in range(0, len(bgs_county_gdf))}
#         name_columns = {i:sites_county_gdf.iloc[i]['id_site'] for i in range(0, len(sites_county_gdf))}
#
#         # Initialize blank matrix
#         dist_to_site_matrix = np.NaN*np.zeros((len(bgs_county_gdf), len(sites_county_gdf)))
#         dist_to_site_df = pd.DataFrame(dist_to_site_matrix)
#
#         dist_to_site_df.rename(index = name_index, columns = name_columns, inplace = True)
#
#         # Build matrix
#         print("Measuring distances for " + county)
#         num_bgs = 0
#         for _,bg_row in bgs_county_gdf.iterrows():
#             num_bgs += 1
#             if num_bgs%10 == 0:
#                 print(num_bgs)
#             # node_origin = get_coords_and_nearest_node(bg_row['GISJOIN'], 'GISJOIN', bgs_county_gdf, county_graph)
#             node_origin = get_coords_and_nearest_node(bg_row['GISJOIN'], 'GISJOIN', bgs_county_gdf, graph_california)
#
#             sites_nearby = get_nearby_sites_lat_long(bg_row, sites_county_gdf, k_neighbors, max_distance)
#
#             for site in sites_nearby:
#
#                 # node_target = get_coords_and_nearest_node(site, 'id_site', sites_county_gdf, county_graph)
#                 node_target = get_coords_and_nearest_node(site, 'id_site', sites_county_gdf, graph_california)
#
#                 try:
#                     # travel_dist_m = nx.shortest_path_length(county_graph, node_origin, node_target, weight = 'length')
#                     travel_dist_m = nx.shortest_path_length(graph_california, node_origin, node_target, weight = 'length')
#
#                     dist_to_site_df.loc[bg_row['GISJOIN'], site] = round(travel_dist_m/1609.344, 2)
#
#                 except:
#                     dist_to_site_df.loc[bg_row['GISJOIN'], site] = None
#
#         # #Write output to csv
#         dist_to_site_df.to_csv(output_file_name)
#         # %% codecell
