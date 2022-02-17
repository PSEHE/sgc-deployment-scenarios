# import plotly.graph_objects as go # or plotly.express as px
# import pandas as pd
import os
gpd
import geopandas as gpd
import fiona
# import numpy as np

# us_cities = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")
# hubs_df = pd.read_csv(os.path.join("data","candidate_site_campuses_2021-11-17","candidate_sites_campuses.csv"),
                      # index_col='id_site')
blockgroup_gdf = gpd.read_file(os.path.join("data","bg_ca_19","blockgroup_CA_19.shp"))
# blockgroup_df = blockgroup_gdf[["INTPTLAT","INTPTLON","GISJOIN"]].copy().set_index("GISJOIN")

# # no_paths_df = pd.read_csv(os.path.join("data","no_path_founds_contracosta.csv"))
# distmatrix_df = pd.read_csv(os.path.join("data","distmatrix_bbox.csv"))
# distmatrix_df.rename(columns = {"Unnamed: 0":"GISJOIN"},inplace=True)
# distmatrix_df.set_index("GISJOIN",inplace=True)
#
# # run_string = "p_med_min_block_100"
# run_string = "max_coverage_50_bgs_5_hubs"
# var_prop_served=pd.read_csv(os.path.join("results",run_string+"var_prop_served.csv"))
# var_prop_served.rename(columns = {"Unnamed: 0":"GISJOIN"},inplace=True)
# var_prop_served.set_index("GISJOIN",inplace=True)
# var_hub_yn = pd.read_csv(os.path.join("results",run_string+"var_hub_yn.csv"))
# #########
#
# dists = dict()
# r=6
# for r in range(distmatrix_df.shape[0]):
#     idx_real = np.where(distmatrix_df.iloc[r,:].notnull())
#     dist_dict = dict(distmatrix_df.iloc[r,idx_real[0]])
#     dists[distmatrix_df.index[r]] = dist_dict
#
# pairs = dict()
# for r in range(var_prop_served.shape[0]):
#     idx_real = np.where((var_prop_served.iloc[r,:].notnull())&(var_prop_served.iloc[r,:]>0))
#     pair_dict = dict(var_prop_served.iloc[r,idx_real[0]])
#     pairs[var_prop_served.index[r]] = pair_dict
#
# fig = go.Figure(go.Scattermapbox(lat=hubs_df["LAT"], lon=hubs_df["LON"],
#                                  mode='markers',
#                                 marker=go.scattermapbox.Marker(
#                                     size=10,
#                                     color='rgb(255, 0, 0)',
#                                     opacity=0.7
#                                 ),
#                                 text=hubs_df["name_site"],
#                                 hoverinfo='text'
#                                  # hovertext=hubs_df["name_site"],
#                                  # hover_data=["cat_site"],
#                                  # color_discrete_sequence=["fuchsia"],
#                                  # zoom=5,
#                                  # height=600
#                                  )
#                 )
#
#
# fig.add_trace(go.Scattermapbox(lat=blockgroup_gdf["INTPTLAT"], lon=blockgroup_gdf["INTPTLON"],
#                                  mode='markers',
#                                 marker=go.scattermapbox.Marker(
#                                     size=10,
#                                     color='rgb(0, 0, 0)',
#                                     opacity=0.7
#                                 ),
#                                 text=blockgroup_gdf["GISJOIN"],
#                                 hoverinfo='text'
#                                  # hovertext=hubs_df["name_site"],
#                                  # hover_data=["cat_site"],
#                                  # color_discrete_sequence=["fuchsia"],
#                                  # zoom=5,
#                                  # height=600
#                                  )
#                 )
#
# plot_no_paths = False
# if plot_no_paths:
#     lons_no_path = []
#     lats_no_path = []
#     for row in no_paths_df.itertuples():
#         if np.random.rand(1)<1.05:
#             lons_no_path.append(float(blockgroup_df.loc[row[2],"INTPTLON"]))
#             lats_no_path.append(float(blockgroup_df.loc[row[2],"INTPTLAT"]))
#             lons_no_path.append(float(hubs_df.loc[str(row[3]),"LON"]))
#             lats_no_path.append(float(hubs_df.loc[str(row[3]),"LAT"]))
#             lons_no_path.append(None)
#             lats_no_path.append(None)
#
#     fig.add_trace(go.Scattermapbox(
#         mode = "lines",
#         lon = lons_no_path,
#         lat = lats_no_path,
#         marker = {'size': 10}))
#
# plot_all_nearbys = False
# if plot_all_nearbys:
#     lons_dists = []
#     lats_dists = []
#     names_dists = []
#     for bg in dists:
#         for hub in dists[bg]:
#             if np.random.rand(1)<1.01:
#                 # if dists[bg][hub] == 0.0:
#                 lons_dists.append(float(blockgroup_df.loc[bg,"INTPTLON"]))
#                 lats_dists.append(float(blockgroup_df.loc[bg,"INTPTLAT"]))
#                 lons_dists.append(float(hubs_df.loc[str(hub),"LON"]))
#                 lats_dists.append(float(hubs_df.loc[str(hub),"LAT"]))
#                 names_dists.append(str(dists[bg][hub]))
#                 lons_dists.append(None)
#                 lats_dists.append(None)
#                 names_dists.append(None)
#
#     fig.add_trace(go.Scattermapbox(
#         mode = "lines",
#         lon = lons_dists,
#         lat = lats_dists,
#         text = names_dists,
#         hovertext = names_dists,
#         marker = {'size': 10}))
#
# lons_pairs = []
# lats_pairs = []
# names_pairs = []
# for bg in pairs:
#     for hub in pairs[bg]:
#         if np.random.rand(1)<1.01:
#             # if dists[bg][hub] == 0.0:
#             lons_pairs.append(float(blockgroup_df.loc[bg,"INTPTLON"]))
#             lats_pairs.append(float(blockgroup_df.loc[bg,"INTPTLAT"]))
#             lons_pairs.append((float(blockgroup_df.loc[bg,"INTPTLON"])+float(hubs_df.loc[str(hub),"LON"]))/2)
#             lats_pairs.append((float(blockgroup_df.loc[bg,"INTPTLAT"])+float(hubs_df.loc[str(hub),"LAT"]))/2)
#             lons_pairs.append(float(hubs_df.loc[str(hub),"LON"]))
#             lats_pairs.append(float(hubs_df.loc[str(hub),"LAT"]))
#             names_pairs.append("Proportion of demand: " + str(pairs[bg][hub]))
#             names_pairs.append("Proportion of demand: " + str(pairs[bg][hub]))
#             names_pairs.append("Proportion of demand: " + str(pairs[bg][hub]))
#             lons_pairs.append(None)
#             lats_pairs.append(None)
#             names_pairs.append(None)
#
# fig.add_trace(go.Scattermapbox(
#     mode = "lines",
#     lon = lons_pairs,
#     lat = lats_pairs,
#     text = names_pairs,
#     hovertext = names_pairs,
#     marker = {'size': 10}))
#
#
# #
# # line_mapbox
# # fig.add_trace(go.line_mapbox(lat=blockgroup_gdf["INTPTLAT"], lon=blockgroup_gdf["INTPTLON"],
# #                                  mode='markers',
# #                                 marker=go.scattermapbox.Marker(
# #                                     size=10,
# #                                     color='rgb(0, 0, 0)',
# #                                     opacity=0.7
# #                                 ),
# #                                 text=blockgroup_gdf["GISJOIN"],
# #                                 hoverinfo='text'
# #                                  # hovertext=hubs_df["name_site"],
# #                                  # hover_data=["cat_site"],
# #                                  # color_discrete_sequence=["fuchsia"],
# #                                  # zoom=5,
# #                                  # height=600
# #                                  )
# #                 )
#
#
# # import plotly.express as px
#
# # fig_choro = px.choropleth(blockgroup_gdf,
# #                    geojson=blockgroup_gdf.geometry,
# #                    locations=blockgroup_gdf.index,
# #                    # color="Joly",
# #                    # projection="mercator"
# #                    )
# #
# # fig.add_trace(fig_choro)
#
# # fig.update_geos(fitbounds="locations", visible=False)
# # fig.show()
# # fig = go.Figure(go.Scattermapbox(mode = "lines", fill = "toself",
# #                                  lon = [-10, -10, 8, 8, -10, None, 30, 30, 50, 50, 30, None, 100, 100, 80, 80, 100],
# #                                  lat = [30, 6, 6, 30, 30,    None, 20, 30, 30, 20, 20, None, 40, 50, 50, 40, 40]))
# # fig = px.scatter_mapbox(hubs_df, lat="LAT", lon="LON", hover_name="name_site",
# #                         hover_data=["cat_site"],
# #                         color_discrete_sequence=["fuchsia"], zoom=5,
# #                         height=600)
#
# fig.update_layout(mapbox_style="open-street-map",
#                   mapbox=dict(center=dict(lat=38,lon=-94),
#                                zoom=3
#                                ),
#                   height = 700,
#                   )
# # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
#
# import dash
# from dash import dcc
# from dash import html
#
# app = dash.Dash()
# app.layout = html.Div([
#     html.H2(children='SGC Hubs'),
#     dcc.Graph(figure=fig)
# ])
#
# app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter
