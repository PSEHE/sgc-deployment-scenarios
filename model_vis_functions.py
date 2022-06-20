# # Plots to add
# 1. Histogram of distances travelled
# 2. Histogram of total fractions served
# 3.

import plotly.graph_objects as go # or plotly.express as px
import pandas as pd
import os
import geopandas as gpd
import numpy as np
import plotly.express as px

# MAPBOX_API_KEY = "pk.eyJ1IjoieXVudXNraW5rIiwiYSI6ImNrenNrNHlscDcza3gyd25majU1cXozdmYifQ.SYnTOqlbYlBHRkR-odr9fw"

# px.set_mapbox_access_token(MAPBOX_API_KEY)
# from data_cleaning import hub_occ_dict
# hub_occ_dict
# hub_occ_df = pd.Series(hub_occ_dict)
# hub_occ_df.to_csv("hub_occ_df.csv")
# hub_occ_df = pd.read_csv("hub_occ_df.csv")
# hub_occ_df.rename(columns = {"Unnamed: 0":"id_site",'0':'maximum_occupancy'},inplace=True)
# hub_occ_df.set_index("id_site",inplace=True)

# us_cities = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")
# hubs_df = pd.read_csv(os.path.join("data","candidate_site_campuses_2021-11-17","candidate_sites_campuses.csv"),
#                       index_col='id_site')
# blockgroup_gdf = gpd.read_file(os.path.join("data","bg_ca_19","blockgroup_CA_19.shp"))
# blockgroup_df = blockgroup_gdf[["INTPTLAT","INTPTLON","GISJOIN"]].copy().set_index("GISJOIN")
# blockgroup_gdf = blockgroup_gdf.set_index("GISJOIN")

# no_paths_df = pd.read_csv(os.path.join("data","no_path_founds_contracosta.csv"))
# distmatrix_df = pd.read_csv(os.path.join("data","distmatrix_bbox.csv"))
# distmatrix_df.rename(columns = {"Unnamed: 0":"GISJOIN"},inplace=True)
# distmatrix_df.set_index("GISJOIN",inplace=True)

# run_string = "p_med_min_block_100"
# var_prop_served.loc[:,hubs_not_built].sum(axis=0).unique()
# var_prop_served.loc[:,hubs_built].sum(axis=0).unique()


#########

import deployment_models

def map_model_results(model,blockgroup_df,blockgroup_gdf,hubs_df,distmatrix_df):
    var_hub_yn, var_prop_served = deployment_models.get_vars(model)
    hubs_not_built = var_hub_yn.index[var_hub_yn[0]==0]
    hubs_not_built = [str(h) for h in hubs_not_built if str(h) in var_prop_served.columns]
    hubs_built = var_hub_yn.index[var_hub_yn[0]==1]
    hubs_built = [str(h) for h in hubs_built if str(h) in var_prop_served.columns]

    hubs_built_df = hubs_df.loc[hubs_built,:]
    hubs_not_built_df = hubs_df.loc[hubs_not_built,:]

    blockgroup_df = blockgroup_df.loc[var_prop_served.index.to_list(),:]
    blockgroup_gdf = blockgroup_gdf.loc[var_prop_served.index.to_list(),:]

    dists = dict()
    for r in range(distmatrix_df.shape[0]):
        idx_real = np.where(distmatrix_df.iloc[r,:].notnull())
        dist_dict = dict(distmatrix_df.iloc[r,idx_real[0]])
        dists[distmatrix_df.index[r]] = dist_dict

    pairs = dict()
    for r in range(var_prop_served.shape[0]):
        idx_real = np.where((var_prop_served.iloc[r,:].notnull())&(var_prop_served.iloc[r,:]>0))
        pair_dict = dict(var_prop_served.iloc[r,idx_real[0]])
        pairs[var_prop_served.index[r]] = pair_dict

    # BUILT HUBS
    fig_map = go.Figure(go.Scattermapbox(lat=hubs_built_df["LAT"], lon=hubs_built_df["LON"],
                                     mode='markers',
                                    marker=go.scattermapbox.Marker(
                                        size=20*np.sqrt(hubs_built_df["kw_occ"])/np.max(np.sqrt(hubs_built_df["kw_occ"])),
                                        color='rgb(255, 0, 0)',
                                        opacity=0.7,
                                        # symbol = "castle"
                                    ),
                                    name = "Built Hubs",
                                    # marker_symbol = 'circle-open',
                                    text=hubs_built_df["name_site"],
                                    hoverinfo='text'
                                     # hovertext=hubs_df["name_site"],
                                     # hover_data=["cat_site"],
                                     # color_discrete_sequence=["fuchsia"],
                                     # zoom=5,
                                     # height=600
                                     )
                    )

    # UNBUILT HUBS
    fig_map.add_trace(go.Scattermapbox(lat=hubs_not_built_df["LAT"], lon=hubs_not_built_df["LON"],
                                     mode='markers',
                                    marker=go.scattermapbox.Marker(
                                        size=20*np.sqrt(hubs_not_built_df["kw_occ"])/np.max(np.sqrt(hubs_not_built_df["kw_occ"])),
                                        color='rgb(185, 0, 0)',
                                        opacity=0.4
                                    ),
                                    text=hubs_not_built_df["name_site"],
                                    hoverinfo='text',
                                    name = "Unbuilt Hubs",
                                     # hovertext=hubs_df["name_site"],
                                     # hover_data=["cat_site"],
                                     # color_discrete_sequence=["fuchsia"],
                                     # zoom=5,
                                     # height=600
                                     )
                    )


    fig_map.add_trace(go.Scattermapbox(lat=blockgroup_df["INTPTLAT"], lon=blockgroup_df["INTPTLON"],
                                     mode='markers',
                                    marker=go.scattermapbox.Marker(
                                        size=10*np.sqrt(blockgroup_df["CES"])/np.max(np.sqrt(blockgroup_df["CES"])),
                                        # size=20*np.sqrt(blockgroup_df["population"])/np.max(np.sqrt(blockgroup_df["population"])),
                                        color='rgb(0, 0, 205)',
                                        opacity=0.7
                                    ),
                                    text=blockgroup_df.index,
                                    hoverinfo='text',
                                    name = "Blockgroups",
                                     # hovertext=hubs_df["name_site"],
                                     # hover_data=["cat_site"],
                                     # color_discrete_sequence=["fuchsia"],
                                     # zoom=5,
                                     # height=600
                                     )
                    )

    lons_pairs = []
    lats_pairs = []
    names_pairs = []
    for bg in pairs:
        for hub in pairs[bg]:
            if np.random.rand(1)<1.01:
                # if dists[bg][hub] == 0.0:
                lons_pairs.append(float(blockgroup_df.loc[bg,"INTPTLON"]))
                lats_pairs.append(float(blockgroup_df.loc[bg,"INTPTLAT"]))
                lons_pairs.append((float(blockgroup_df.loc[bg,"INTPTLON"])+float(hubs_df.loc[str(hub),"LON"]))/2)
                lats_pairs.append((float(blockgroup_df.loc[bg,"INTPTLAT"])+float(hubs_df.loc[str(hub),"LAT"]))/2)
                lons_pairs.append(float(hubs_df.loc[str(hub),"LON"]))
                lats_pairs.append(float(hubs_df.loc[str(hub),"LAT"]))
                names_pairs.append(str(bg))
                names_pairs.append("Proportion of demand: " + str(pairs[bg][hub]))
                names_pairs.append(str(hub))
                lons_pairs.append(None)
                lats_pairs.append(None)
                names_pairs.append(None)

    fig_map.add_trace(go.Scattermapbox(
        mode = "lines",
        lon = lons_pairs,
        lat = lats_pairs,
        text = names_pairs,
        hovertext = names_pairs,
        marker = {'size': 10},
        name = "Assigned Demand"))

    # carto-darkmatter, carto-positron, open-street-map, stamen-terrain, stamen-toner, stamen-watercolor, white-bg

    fig_map.update_layout(mapbox=dict(center=dict(lat=38,lon=-94),
                                   zoom=3
                                   ),
                      mapbox_style="open-street-map",
                      # mapbox_style="carto-darkmatter",
                      height = 700,
                      )

    fig_map.update_layout(legend=dict(title_font_family="Times New Roman",
                              font=dict(size= 20)))

    return fig_map

# fig_capacity_cdf = px.ecdf(hub_occ_df.loc[hubs_built], x="maximum_occupancy")
