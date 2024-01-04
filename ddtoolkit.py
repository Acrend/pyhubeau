import numpy as np
import pandas as pd
import json

class PiezoTool():
    def __init__(self,piezo_folder_path="piezo\\"):
        list_station_piezo = pd.read_csv(piezo_folder_path+"list_station_piezo.csv")
        with open(piezo_folder_path + "options\\color_label.json","r") as f:
            self.color_label = json.load(f)
        with open(piezo_folder_path + "options\\relabel.json","r") as f:
            self.relabel = json.load(f)

        # we do this operation cause of the stupide french language and the fact that it use comma as decimal separator
        # we are trash talking american about there imperial system but we are actualy as dump as them >:(
        seuil_columns = [col for col in list_station_piezo.columns if col.startswith('seuil_')]
        try:
            for col in seuil_columns:
                list_station_piezo[col] = pd.to_numeric(list_station_piezo[col].astype(str).str.replace(',', '.'), errors='coerce')
        except:
            pass
        
        self.station_piezo_options = {}
        for row in list_station_piezo.iterrows():
            self.station_piezo_options[row[1].code_station] = {"title":row[1].departement + ' - ' + row[1].commune,'thresold':dict(row[1][seuil_columns]),"water_table":row[1].nappe}

        self.station_piezo_list = list(list_station_piezo['code_station'])

class HydroTool():
    def __init__(self,hydro_folder_path="hydro\\"):
        list_site_hydro = pd.read_csv(hydro_folder_path+"list_site_hydro.csv")
        with open(hydro_folder_path + "options\\color_label.json","r") as f:
            self.color_label = json.load(f)
        with open(hydro_folder_path + "options\\relabel.json","r") as f:
            self.relabel = json.load(f)

        # we do this operation cause of the stupide french language and the fact that it use comma as decimal separator
        # we are trash talking american about there imperial system but we are actualy as dump as them >:(
        seuil_columns = [col for col in list_site_hydro.columns if col.startswith('seuil_')]
        try:
            for col in seuil_columns:
                list_site_hydro[col] = pd.to_numeric(list_site_hydro[col].astype(str).str.replace(',', '.'), errors='coerce')
        except:
            pass
        
        self.site_hydro_options = {}
        for row in list_site_hydro.iterrows():
             self.site_hydro_options[row[1].code_site] = {"title":row[1].titre_graphique,'thresold':dict(row[1][seuil_columns])}

        self.site_hydro_list = list(list_site_hydro['code_site'])