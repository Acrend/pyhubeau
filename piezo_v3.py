from pyhubeau import RequestDataHubeau, StationPiezoApp
from ddtoolkit import PiezoTool
import pandas as pd

pt = PiezoTool()

RDH = RequestDataHubeau()
SPA = StationPiezoApp()

for i,station_piezo_id in enumerate(pt.station_piezo_list):
    station_piezo_table = RDH.get_station_piezo_chroniques(station_piezo_id)
    station_piezo_data, month_percentile = SPA.gen_station_piezo_data_based_on_all(station_piezo_table)
    graph_site_data = SPA.gen_graph_site_data(station_piezo_data, month_percentile)

    if SPA.water_table.get(pt.station_piezo_options[station_piezo_id]['water_table']):
        SPA.water_table[pt.station_piezo_options[station_piezo_id]['water_table']].append(station_piezo_table[['niveau_nappe_eau']])
    else:
        SPA.water_table[pt.station_piezo_options[station_piezo_id]['water_table']] = [station_piezo_table[['niveau_nappe_eau']]]

    SPA.matplot_graph_generation(graph_site_data,
                                past_year_number=4,
                                title=pt.station_piezo_options[station_piezo_id]['title'],
                                color_label=pt.color_label,
                                relabel=pt.relabel,
                                thresold=pt.station_piezo_options[station_piezo_id]['thresold'],
                                show=False,
                                save_fig=True,
                                save_path="piezo\\graph_station_piezo\\",
                                save_name=f'{i:05}')
    
for key in list(SPA.water_table.keys()):
    water_table_table = pd.concat(SPA.water_table[key],axis=1) # yeah water_table_table kinda suck but what can I do ? a "nappe" in english is water table and it's logical that a table of water table is call water_table_table
    #water_table_table = SPA.gen_normalize_water_table(water_table_table)
    water_table_table = SPA.gen_standardize_water_table(water_table_table)
    water_table_data, month_percentile = SPA.gen_station_piezo_data_based_on_all(water_table_table)
    graph_site_data = SPA.gen_graph_site_data(water_table_data, month_percentile)

    SPA.matplot_graph_generation(graph_site_data,
                                past_year_number=4,
                                title=key,
                                color_label=pt.color_label,
                                relabel=pt.relabel,
                                thresold=None,
                                show=False,
                                save_fig=True,
                                save_path="piezo\\graph_nappe\\",
                                save_name=key)