# This script produces a dictionary that links site IDs to the block group
# GEOIDs that the hubs are in
import os
from datetime import datetime
import pandas as pd
import numpy as np
from pyomo.environ import *
import pyomo.opt as pyopt

import geopandas as gpd
import pandas as pd
import numpy as np
from statistics import mean

import itertools

ca_albers_nad83 = 'NAD_1983_California_Teale_Albers_FtUS'
nad83 = 'EPSG:4269'
wgs84 = 'EPSG:4326'

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

sites_in_bgs = gpd.tools.sjoin(sites_gdf, bgs_gdf, predicate="within", how='inner')

sites_bgs_dict = dict(zip(sites_in_bgs['id_site'], sites_in_bgs['GISJOIN']))
