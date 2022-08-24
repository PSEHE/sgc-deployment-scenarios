# This script creates a walking graph for Contra Costa County which also
# includes BART and AC Transit lines.
# Code from: http://kuanbutts.com/2018/12/24/peartree-with-walk-network/

import osmnx as ox
from osmnx import utils_graph
import networkx as nx

import peartree as pt
from peartree.graph import generate_empty_md_graph, populate_graph
from peartree.paths import (FALLBACK_STOP_COST_DEFAULT,
                            _calculate_means_default, get_representative_feed)
from peartree.summarizer import (generate_edge_and_wait_values,
                                 generate_summary_edge_costs,
                                 generate_summary_wait_times)
import geopandas as gpd
import pandas as pd
import numpy as np
from statistics import mean
from sklearn.neighbors import KDTree

import matplotlib.pyplot as plt
import shapely
from shapely.geometry import Point
from sklearn.neighbors import KDTree
import folium
import requests

import os

import warnings

import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

import peartree as pt

nad83 = 'EPSG:4269'

def remove_isolated_nodes_grom_graph(G):
    broken_idx = []
    for i, n in G.nodes(data=True):
        try:
            float(n['x'])
        except:
            broken_idx.append(i)

    for bad_n in broken_idx:
        # Make sure they do not conenct to anything
        if len(G[bad_n]) > 0:
            # If they do try to add relevant information to the nodes
            print(bad_n)
        else:
            # So just drop them
            G.remove_node(bad_n)
    return G

def find_nodes_from_coords(nodes, xcoord, ycoord, buffer_dist=0.005):
    """Helper function to quickly get a subset of nodes close to certain point."""
    p = Point(xcoord, ycoord)
    # Buffer
    a = p.buffer(buffer_dist)
    # Find nodes
    selected_nodes = nodes.loc[nodes.intersects(a)]
    return selected_nodes

def get_closest(src_points, candidates, k_neighbors=2):
    """Find nearest neighbors for all source points from a set of candidate points"""

    # Create tree
    tree = KDTree(candidates, leaf_size=2)

    # Find closest points and distances
    distances, indices = tree.query(src_points, k=k_neighbors)

    # Transpose to get distances and indices into arrays
    distances = distances.transpose()
    indices = indices.transpose()

    # Get closest points and distances (i.e. array at index 0)
    closest = indices[0]
    closest_dist = distances[0]

    # Return indices and distances
    return (closest, closest_dist)

def convert_decimaldegree_to_km(gdf, src_col, target_col='dist_km'):
    """
    Convert decimal degree distances of the src_col into kilometers using naive conversion.
    Note: Assumes that the input GeoDataFrame has WGS84 coordinate reference system.
    Based on: https://en.wikipedia.org/wiki/Decimal_degrees

    Formula to convert 1 decimal degree to km:
    N/S or E/W at equator	E/W at 23N/S	E/W at 45N/S	E/W at 67N/S
    111.32 km	            102.47 km	    78.71 km	    43.496 km
    """
    # Check the latitude of the data
    maxy = abs(gdf.bounds.maxy.max())

    # Specify the conversion factor between decimal degrees and kilometers
    if maxy < 23:
        conversion_factor = 111.32
    elif maxy < 45:
        conversion_factor = 102.47
    elif maxy < 67:
        conversion_factor = 78.71
    else:
        conversion_factor = 43.496

    # Calculate the distance in kilometer
    gdf[target_col] = gdf[src_col] * conversion_factor
    return gdf

def get_graph_extent(G):
    """Returns the convex hull of the given graph (G)"""
    # We need a coverage area, based on the points from the
    # New Orleans GTFS data, which we can pull from the peartree
    # network graph by utilizing coordinate values and extracting
    # a convex hull from the point cloud
    boundary = gpd.GeoSeries(
        [Point(n['x'], n['y']) for i, n in G.nodes(data=True)]
        ).unary_union.convex_hull
    return boundary

def get_node_info(G, node_id):
    """Return node attributes as a dictionary for the specified node_id"""
    return G.nodes.get(node_id)

def convert_walk_distance_to_seconds(G, walk_speed_kmph=4.5):
    """Converts OSM distances to travel times based on given walk speed"""
    # Make a copy of the graph in case we make a mistake
    Gwalk_adj = G.copy()

    # Iterate through and convert lengths to seconds
    for from_node, to_node, edge in Gwalk_adj.edges(data=True):
        orig_len = edge['length']

        # Note that this is a MultiDiGraph so there could
        # be multiple indices here, I naively assume this is not
        # the case
        Gwalk_adj[from_node][to_node][0]['orig_length'] = orig_len

        # Conversion of walk speed and into seconds from meters
        kmph = (orig_len / 1000) / walk_speed_kmph
        in_seconds = kmph * 60 * 60
        Gwalk_adj[from_node][to_node][0]['length'] = in_seconds

        # And state the mode, too
        Gwalk_adj[from_node][to_node][0]['mode'] = 'walk'
    return Gwalk_adj

def add_boarding_cost_to_graph_nodes(G, boarding_cost=0):
    """All nodes in the graph needs to have a boarding cost (even if they are for walking)"""
    for i, node in G.nodes(data=True):
        G.nodes[i]['boarding_cost'] = boarding_cost
    return G

def get_route_edges(edges, route_nodes):
    # Get route edges
    route_edges = gpd.GeoDataFrame()
    start_n = route_nodes[0]
    for end_n in route_nodes[1:-1]:
        e = edges.loc[(edges['u']==start_n) & (edges['v']==end_n)]
        route_edges = route_edges.append(e)
        start_n = end_n
    return route_edges

## Public Transit

# Read into graph
start = 7 * 60 * 60
end = 9 * 60 * 60
walk_speed = 4.5  #  kmph
interpolate_times = True
use_multiprocessing = False

# get feed for Contra Costa/Wilmington
#all = pt.get_representative_feed(os.path.join("data","gtfs","gtfs_all.zip"))
all = pt.get_representative_feed(os.path.join("data","gtfs","gtfs_ladot.zip"))
pt_graph = pt.load_feed_as_graph(all, start, end,
                                 walk_speed_kmph=walk_speed,
                                 impute_walk_transfers=True,
                                 use_multiprocessing=True)
pt_graph = ox.project_graph(pt_graph, to_crs = nad83)
pt_nodes, pt_edges = ox.graph_to_gdfs(pt_graph)

# Load in the walking graph for Contra Costa/Wilmington
#output_county = 'contracosta'
#walk_graph = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf' + output_county + '.graphml'))
output_area = 'wilmington'
walk_graph = ox.load_graphml(os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_' + output_area + '.graphml'))
# Convert walk distances to travel times
walk_graph = convert_walk_distance_to_seconds(walk_graph, walk_speed_kmph=walk_speed)
walk_graph = ox.project_graph(walk_graph, to_crs = nad83)

# Add boarding cost to the walking nodes (should be 0)
walk_graph = add_boarding_cost_to_graph_nodes(walk_graph, 0)
walk_graph = nx.convert_node_labels_to_integers(walk_graph)

# Get walk nodes
walk_nodes, walk_edges = ox.graph_to_gdfs(walk_graph)

#For each public transport stop, find closest node from street network and
# calculate the walk distance between the nodes
# Get walk node coordinates
walk_node_coords = np.array(walk_nodes['geometry'].apply(lambda geom: (geom.x, geom.y)).to_list())
# Get transport stop coordinates
pt_node_coords = np.array(pt_nodes['geometry'].apply(lambda geom: (geom.x, geom.y)).to_list())
# Find closest street network nodes for each stop
closest, closest_distances = get_closest(src_points=pt_node_coords, candidates=walk_node_coords)

# Create edges between the nodes
walk_nodes_copy = walk_nodes.copy().reset_index()
#closest_ids = walk_nodes_copy.loc[closest, 'index']
#pt_nodes['closest_street_node_id'] = closest_ids.values

pt_nodes['closest_street_node_id'] = closest
pt_nodes['closest_street_node_dist'] = closest_distances
# Convert the distance between public transport stops and street network nodes into travel time (based on walk speed)
# Note: use approximate distance in meters (convert from WGS84)
pt_nodes = convert_decimaldegree_to_km(pt_nodes, src_col='closest_street_node_dist',
                                       target_col='dist_km')

pt_nodes['closest_street_node_time'] = (pt_nodes['dist_km'] / walk_speed)*60*60  # in seconds

# Merge transit network and walk network into the same graph
# Merge public transport graph on top of the walk graph
G = walk_graph.copy()

# Instantiate a list of new edges to add
edges_to_add = []
node_ids_to_add = []
node_ids = []

#Create connecting links between street network and PT stops
# (links needs to be placed in both directions)
# Second add the connecting links between graphs
for stop_idx, stop in pt_nodes.iterrows():

    # ID of the closest street network node (use string always)
    closest_node_id = stop['closest_street_node_id']
    # Walk time in seconds
    walk_dist_t = stop['closest_street_node_time']
    # Walk distance in meters
    walk_dist_m = stop['dist_km'] * 1000

    # Add edge to direction 1
    edges_to_add.append({
            'from': stop_idx,
            'to': closest_node_id,
            'length': walk_dist_t,
            'edge_id': None,
            'cost': walk_dist_t,
            'orig_length': walk_dist_m
        })

    # Add edge to direction 2
    edges_to_add.append({
            'from': closest_node_id,
            'to': stop_idx,
            'length': walk_dist_t,
            'edge_id': None,
            'cost': walk_dist_t,
            'orig_length': walk_dist_m
        })

G = nx.compose(G, pt_graph)

# Add in connecting edges
for new_edge in edges_to_add:
    if new_edge['length'] >= 0 and new_edge['cost'] >= 0:
        if (new_edge['from'] in G) and (new_edge['to'] in G):
            G.add_edge(new_edge['from'],
                       new_edge['to'],
                       length=new_edge['length'],
                       edge_id=new_edge['edge_id'],
                       cost=new_edge['cost'])
    else:
        print('Skipping due to negative edge cost')
        print(new_edge['length'], new_edge['cost'])

G = nx.convert_node_labels_to_integers(G)

# Get all nodes and edges of the combined network
#walk_pt_nodes, walk_pt_edges = ox.graph_to_gdfs(G)

# Save the combined graph g_walk_bart_ac_transit as a graphml file.
#ox.save_graphml(G, os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_cf_transit_' + output_area + '.graphml'))
ox.save_graphml(G, os.path.join(os.getcwd(), 'data', 'graphs', 'graph_walk_transit_' + output_area + '.graphml'))
