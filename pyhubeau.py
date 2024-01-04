import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.ticker import StrMethodFormatter, NullFormatter

from scipy import stats

import requests
import os

def hex_to_rgb(hex_str):
    """ #FFFFFF -> [255,255,255] """
    #Pass 16 to the integer function for change of base
    return [int(hex_str[i:i+2], 16) for i in range(1,6,2)]

def rgb_to_hex(rgb_list):
    """ [1,1,1] -> #FFFFFF """

    return "#" f'{rgb_list[0]:02x}'f'{rgb_list[1]:02x}'f'{rgb_list[2]:02x}'

def get_color_gradient_hex(hex_color_start, hex_color_end, color_number=10):
    assert color_number > 1

    rgb_color_start = np.array(hex_to_rgb(hex_color_start))/255
    rgb_color_end = np.array(hex_to_rgb(hex_color_end))/255

    mix_pcts = [x/(color_number-1) for x in range(color_number)]

    rgb_colors = np.array([((1-mix)*rgb_color_start + (mix*rgb_color_end))*255 for mix in mix_pcts],dtype=int)

    return [rgb_to_hex(rgb_color) for rgb_color in rgb_colors]

def log_norm_vector(vector,percentile=0.5):
        vector_normalize = np.log(vector)
        
        mean = np.mean(vector_normalize)
        std = np.std(vector_normalize)

        return stats.lognorm(std, scale=np.exp(mean)).ppf(percentile)

def gumbel_law_vector(vector,percentile=0.5):
    return np.mean(vector) - (np.sqrt(6)*np.std(vector)*np.log(-np.log(percentile)))/np.pi

class RequestDataHubeau():
    def __init__(self):
        self.request_timeout = 60
        self.request_max_attempt = 1
        self.request_size = 5000
        self.piezo_min_measure_number=90
        self.proxies = {}
        
    def multi_page_json_request(self, url, request_timeout = 60, request_max_attempt = 2, request_size=5000):
        # the purpose of this function is to get all data of a specific request in hubeau, the limit beign 20000
        data_completed = False
        data_json = []
        try_attempt = 0

        url += "&size=" + str(request_size)
        while not data_completed:
            try:
                url_json_result = requests.get(url, timeout=request_timeout,proxies=self.proxies).json()
                data_json = data_json + url_json_result['data']
                url = url_json_result['next']
                if url == None:
                    data_completed = True
                try_attempt = 0
                
            except BaseException as e:
                if type(e) == requests.exceptions.ReadTimeout:
                    print(f"internet connection seems slow, try increasing the request timeout, current is {request_timeout} seconds")
                if type(e) == requests.exceptions.ConnectionError:
                    print("it seems that there is no concection, try to connect to internet")
                else:
                    print(e)
                    print("unidentified request error, maybe maybe try later")
                try_attempt += 1
                if try_attempt > request_max_attempt:
                    data_completed = True
                    print(f"Did not manage to get info on this url : {url}")
        return data_json
    
    def get_hydro_obs_elab(self, site_hydro_id, qm = "QmJ", date_start = None, date_end = None):
        url = 'https://hubeau.eaufrance.fr/api/v1/hydrometrie/obs_elab?code_entite=' + site_hydro_id

        url = url + "&date_debut_obs_elab=" + date_start if (date_start != None) else url
        url = url + "&date_fin_obs_elab=" + date_end if (date_end != None) else url
        url = url + "&grandeur_hydro_elab=" + qm

        data_site_elab = self.multi_page_json_request(url, request_timeout=self.request_timeout, request_max_attempt = self.request_max_attempt, request_size=self.request_size)
        if not data_site_elab:
            return data_site_elab
        data_site_elab = pd.DataFrame(data_site_elab)
        data_site_elab.date_prod = pd.to_datetime(data_site_elab.date_prod)
        data_site_elab.date_obs_elab = pd.to_datetime(data_site_elab.date_obs_elab)

        data_site_elab = data_site_elab.drop(columns=['longitude','latitude'])
        data_site_elab = data_site_elab.drop_duplicates(subset='date_obs_elab')

        data_site_elab = data_site_elab.set_index('date_obs_elab')

        return data_site_elab

    def get_station_piezo_chroniques(self,station_piezo_id, date_start = None, date_end = None):
        url = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques?code_bss=' + station_piezo_id

        url = url + "&date_debut_mesure=" + date_start if (date_start != None) else url
        url = url + "&date_fin_mesure=" + date_end if (date_end != None) else url

        data_station_piezo = self.multi_page_json_request(url, request_timeout=self.request_timeout, request_max_attempt = self.request_max_attempt, request_size=self.request_size)
        if not data_station_piezo:
            return data_station_piezo
        data_station_piezo = pd.DataFrame(data_station_piezo)
        
        data_station_piezo = data_station_piezo[data_station_piezo.qualification=="Correcte"]
        data_station_piezo = data_station_piezo.drop(columns=['urn_bss','timestamp_mesure','qualification'])
        data_station_piezo.date_mesure = pd.to_datetime(data_station_piezo.date_mesure)
        data_station_piezo = data_station_piezo.drop_duplicates(subset='date_mesure')
        
        data_station_piezo = data_station_piezo.set_index('date_mesure')
        data_station_piezo = data_station_piezo.sort_index()

        return data_station_piezo

    def get_site_hydro_info(self):
        site_hydro_mapping = {'coordonnee_x_site':'float64','coordonnee_y_site':'float64',
                            'longitude_site':'float64','latitude_site':'float64','altitude_site':'float64','surface_bv':'float32'}
        url = f"https://hubeau.eaufrance.fr/api/v1/hydrometrie/referentiel/sites?format=json"
        site_hydro_table = self.multi_page_json_request(url, request_timeout = self.request_timeout, request_max_attempt = self.request_max_attempt, request_size=self.request_size)
        site_hydro_table = pd.DataFrame(site_hydro_table)

        return site_hydro_table

    def get_station_hydro_info(self):
        url = f"https://hubeau.eaufrance.fr/api/v1/hydrometrie/referentiel/stations?format=json"
        station_hydro_table = self.multi_page_json_request(url, request_timeout = self.request_timeout, request_max_attempt = self.request_max_attempt, request_size=self.request_size)
        station_hydro_table = pd.DataFrame(station_hydro_table)

        return station_hydro_table
    
    def get_station_piezo_info(self):
        url = f"https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?format=json&nb_mesures_piezo_min={self.piezo_min_measure_number}"
        station_piezo_table = self.multi_page_json_request(url, request_timeout = self.request_timeout, request_max_attempt = self.request_max_attempt, request_size=self.request_size)
        station_piezo_table = pd.DataFrame(station_piezo_table)

        return station_piezo_table

class SiteHydroApp():
    def gen_site_hydro_data(self,site_hydro_data,site_hydro_data_limited,percentile_list=[0.95,0.8,0.5,0.2,0.05]):
        month_percentile = pd.DataFrame(index=np.linspace(1,12,12,dtype=int),columns=['percentile'])
        month_percentile = month_percentile
        for percentile in percentile_list:
            month_group = site_hydro_data_limited['percentile'].groupby(site_hydro_data_limited.index.month).apply(log_norm_vector,percentile)
            month_percentile = month_percentile.join(month_group,rsuffix=f"_{int(percentile*100):02}")

        month_percentile = month_percentile.drop(columns=['percentile'])
        site_hydro_data = site_hydro_data.join(month_percentile,on=site_hydro_data.index.month)

        return site_hydro_data, month_percentile
    
    def gen_site_hydro_data_based_on_all(self,site_hydro_table,percentile_list=[0.95,0.8,0.5,0.2,0.05]):
        site_hydro_data = site_hydro_table[['resultat_obs_elab','libelle_statut','libelle_methode','libelle_qualification']].copy()
        site_hydro_data[site_hydro_data['resultat_obs_elab']<=0] = None # filter negative value for the log operation
        site_hydro_data = site_hydro_data.rename(columns={'resultat_obs_elab':'percentile'})

        site_hydro_data, month_percentile = self.gen_site_hydro_data(site_hydro_data,site_hydro_data,percentile_list)
        
        site_hydro_data = site_hydro_data.rename(columns={'percentile':'resultat_obs_elab'})

        return site_hydro_data, month_percentile

    def gen_site_hydro_data_based_on_year(self,site_hydro_table,percentile_list=[0.95,0.8,0.5,0.2,0.05],base_year=2010,min_year_number=10):
        site_hydro_data = site_hydro_table[['resultat_obs_elab','libelle_statut','libelle_methode','libelle_qualification']].copy()
        site_hydro_data[site_hydro_data['resultat_obs_elab']<=0] = None # filter negative value for the log operation
        site_hydro_data = site_hydro_data.rename(columns={'resultat_obs_elab':'percentile'})
    
        if (site_hydro_data.index.year.min()) < base_year - min_year_number:
            site_hydro_data_limited = site_hydro_data.copy()
            site_hydro_data_limited = site_hydro_data_limited[site_hydro_data_limited.index.year<base_year]

            site_hydro_data, month_percentile = self.gen_site_hydro_data(site_hydro_data,site_hydro_data_limited,percentile_list)
        else:
            site_hydro_data = None 
            month_percentile = None

        site_hydro_data = site_hydro_data.rename(columns={'percentile':'resultat_obs_elab'})

        return site_hydro_data, month_percentile

    def gen_site_hydro_data_based_on_periode(self,site_hydro_table,percentile_list=[0.95,0.8,0.5,0.2,0.05],min_year=1990,max_year=2020):
        site_hydro_data = site_hydro_table[['resultat_obs_elab','libelle_statut','libelle_methode','libelle_qualification']].copy()
        site_hydro_data[site_hydro_data['resultat_obs_elab']<=0] = None # filter negative value for the log operation
        site_hydro_data = site_hydro_data.rename(columns={'resultat_obs_elab':'percentile'})
    
        if (site_hydro_data.index.year.min() <= min_year) and (site_hydro_data.index.year.max() >= max_year):
            site_hydro_data_limited = site_hydro_data.copy()
            site_hydro_data_limited = site_hydro_data_limited[site_hydro_data_limited.index.year<=max_year]
            site_hydro_data_limited = site_hydro_data_limited[site_hydro_data_limited.index.year>=min_year]

            site_hydro_data, month_percentile = self.gen_site_hydro_data(site_hydro_data,site_hydro_data_limited,percentile_list)
        else:
            site_hydro_data = None 
            month_percentile = None

        site_hydro_data = site_hydro_data.rename(columns={'percentile':'resultat_obs_elab'})

        return site_hydro_data, month_percentile
    
    def gen_graph_site_data(self,site_hydro_data,month_percentile):
        graph_site_data = site_hydro_data[['resultat_obs_elab','libelle_statut','libelle_methode','libelle_qualification']].copy()
        
        min_date = f"{graph_site_data.index.min().year}-01-01"
        max_date = f"{graph_site_data.index.max().year}-12-31"
        calendar = pd.DataFrame(index=pd.date_range(start=min_date,end=max_date))
        calendar = calendar.join(month_percentile,on=calendar.index.month)
        graph_site_data = calendar.join(graph_site_data)
                
        return graph_site_data

    def matplot_graph_generation(self,
    graph_site_data,
    relabel=None,
    color_label=None,
    thresold=None,
    focus_year=None,
    past_year_number=None,
    title='graph',
    save_name='graph',
    save_path='out\\',
    save_fig=False,
    show=False,
    gradient_color_past_year_start="#d013d6",
    gradient_color_past_year_end="#4b8a11"):

        matplot_data = graph_site_data.copy()
        matplot_data = matplot_data[~((matplot_data.index.month == 2) & (matplot_data.index.day==29))]
        matplot_data = matplot_data.sort_index()

        percentile_extract = matplot_data.filter(regex='^percentile',axis=1)

        if not focus_year:
            focus_year = matplot_data.index.year.max()

        elements_color = '#262626'
        fig, ax = plt.subplots(figsize=(22,17),facecolor='#ffffff')

        legend_list = []

        plt.grid(which='major', color='#666666', linestyle='-', alpha=0.1)
        plt.minorticks_on()
        plt.grid(which='minor', color='#999999', linestyle='-', alpha=0.05)
        
        plt.xticks(fontsize=20,color=elements_color)
        plt.yticks(fontsize=20,color=elements_color)

        ax.set_ylabel("Débit du cours d'eau en m$^3$/s",size=25,color=elements_color)

        ax.spines['bottom'].set_color(elements_color)
        ax.spines['top'].set_color(elements_color)
        ax.spines['right'].set_color(elements_color)
        ax.spines['left'].set_color(elements_color)
        ax.set_xlim(1,365)

        ax.set_title(title,size=30,color=elements_color)

        last_date = matplot_data.index.max()
        txt = 'Dernière Mesure:\n' + '        '+ str(last_date)[:10]
        ax.annotate(txt, (0.92, 0.01),fontsize=12,xycoords='axes fraction',rotation=0,color=elements_color)

        y_label_pos = ax.get_yticks()[1:-2]
        y_label_name_reformat = []
        
        day_index = np.linspace(1,365,365)

        for percentile in percentile_extract.columns:
            try:
                plt.plot(day_index,matplot_data[matplot_data.index.year==focus_year][percentile].values,color=color_label[percentile],linewidth = 2.5, alpha=0.8) 
            except:
                plt.plot(day_index,matplot_data[matplot_data.index.year==focus_year][percentile].values,linewidth = 2.5, alpha=0.8) 
            legend_list.append(percentile)

        if past_year_number:
            if past_year_number != 1:
                year_list = np.linspace(focus_year-past_year_number,focus_year-1,past_year_number,dtype=int)
            else:
                year_list = [focus_year-1]
            for i,year in enumerate(year_list):
                color_list = get_color_gradient_hex(hex_color_start=gradient_color_past_year_start, hex_color_end=gradient_color_past_year_end, color_number=len(year_list))
                try:
                    plt.plot(day_index,matplot_data[matplot_data.index.year==year]['resultat_obs_elab'].values,label=str(year),color=color_list[i],linewidth = 5,alpha=0.75,linestyle=':')
                    legend_list.append("Débit du cours d'eau en : " + str(year))
                except:
                    pass
        
        plt.plot(day_index,matplot_data[matplot_data.index.year==focus_year]['resultat_obs_elab'].values,color='#000000',label=str(focus_year),linewidth = 5, alpha=1)
        legend_list.append("Débit du cours d'eau en : " + str(focus_year))

        if thresold:
            thresold_keys = list(thresold.keys())
            for key in thresold_keys:
                if thresold[key]:
                    plt.plot(day_index,thresold[key]*np.ones(365),color=color_label[key],linewidth = 3,in_layout=False,alpha=0.9,linestyle='--')
                    legend_list.append(key[6:])
                
        ax.set_yscale('log')
        if matplot_data['resultat_obs_elab'].min() < 0.01:
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.2f}'))
        else:
            ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.1f}'))

        y_label_pos = ax.get_yticks()[1:-2]
        
        y_label_name_reformat = []
        
        for i in range(len(y_label_pos)):
            if int(y_label_pos[i])==0:
                y_label_name_reformat.append(str(y_label_pos[i]).replace('.',','))
            else:
                y_label_name_reformat.append(str(int(y_label_pos[i])))
        
        ax.set_yticks(y_label_pos)
        ax.set_yticklabels(y_label_name_reformat) 

        month_list = ['Jan.','Fév.','Mars','Avril','Mai','Juin',
                      'Juil.','Aout','Sept.','Oct.','Nov.','Déc.']

        for month_line in [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]:
            plt.axvline(x=month_line, color="#666666",linewidth = 2,in_layout=False,alpha=0.5)

        ax.set_xticks([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334])
        ax.set_xticklabels(month_list,rotation=45)


        box = ax.get_position()
        ax.set_position([box.x0-0.05, box.y0+0.04, box.width*1.1, box.height])

        for i,label in enumerate(legend_list):
            try:
                legend_list[i] = relabel[label]
            except:
                pass

        ax.legend(legend_list, prop={'size': 15},loc='upper center',
                  bbox_to_anchor=(0.5, -0.08),
                  shadow=True,ncol=6)

        if save_fig:
            fig_path = save_path + save_name + '.png'
            try:
                os.makedirs(save_path)
            except:
                pass
            plt.savefig(fig_path, bbox_inches='tight')

        if show:
            plt.show()
        else:
            plt.close(fig)

class StationPiezoApp():
    def __init__(self):
        self.water_table = {}

    def gen_station_piezo_data(self,station_piezo_data,station_piezo_limited,percentile_list=[0.95,0.8,0.5,0.2,0.05]):
        month_percentile = pd.DataFrame(index=np.linspace(1,12,12,dtype=int),columns=['percentile'])
        month_percentile = month_percentile
        for percentile in percentile_list:
            month_group = station_piezo_limited['percentile'].groupby(station_piezo_limited.index.month).apply(gumbel_law_vector,percentile)
            month_percentile = month_percentile.join(month_group,rsuffix=f"_{int(percentile*100):02}")

        month_percentile = month_percentile.drop(columns=['percentile'])
        station_piezo_data = station_piezo_data.join(month_percentile,on=station_piezo_data.index.month)

        return station_piezo_data, month_percentile
    
    def gen_station_piezo_data_based_on_all(self,station_piezo_table,percentile_list=[0.95,0.8,0.5,0.2,0.05]):
        station_piezo_data = station_piezo_table[['niveau_nappe_eau']].copy()
        station_piezo_data = station_piezo_data.rename(columns={'niveau_nappe_eau':'percentile'})

        station_piezo_data, month_percentile = self.gen_station_piezo_data(station_piezo_data,station_piezo_data,percentile_list)
        
        station_piezo_data = station_piezo_data.rename(columns={'percentile':'niveau_nappe_eau'})

        return station_piezo_data, month_percentile

    def gen_graph_site_data(self,station_piezo_data,month_percentile):
        graph_site_data = station_piezo_data[['niveau_nappe_eau']].copy()
        
        min_date = f"{graph_site_data.index.min().year}-01-01"
        max_date = f"{graph_site_data.index.max().year}-12-31"
        calendar = pd.DataFrame(index=pd.date_range(start=min_date,end=max_date))
        calendar = calendar.join(month_percentile,on=calendar.index.month)
        graph_site_data = calendar.join(graph_site_data)
                
        return graph_site_data
    
    def gen_normalize_water_table(self,water_table_data):
        normalize_water_table = (water_table_data - water_table_data.min())/(water_table_data.max()-water_table_data.min())
        normalize_water_table = normalize_water_table.sum(axis=1)/(normalize_water_table.notna().sum(axis=1))
        normalize_water_table = pd.DataFrame(normalize_water_table,columns=['niveau_nappe_eau'])
        return normalize_water_table
    
    def gen_standardize_water_table(self,water_table_data):
        standardize_water_table = (water_table_data - water_table_data.mean())/(water_table_data.std())
        standardize_water_table = standardize_water_table.sum(axis=1)/(standardize_water_table.notna().sum(axis=1))
        standardize_water_table = pd.DataFrame(standardize_water_table,columns=['niveau_nappe_eau'])
        return standardize_water_table

    def matplot_graph_generation(self,
    graph_site_data,
    relabel=None,
    color_label=None,
    thresold=None,
    focus_year=None,
    past_year_number=None,
    title='graph',
    save_name='graph',
    save_path='out\\',
    save_fig=False,
    show=False,
    gradient_color_past_year_start="#d013d6",
    gradient_color_past_year_end="#4b8a11"):

        matplot_data = graph_site_data.copy()
        matplot_data = matplot_data[~((matplot_data.index.month == 2) & (matplot_data.index.day==29))]
        matplot_data = matplot_data.sort_index()

        percentile_extract = matplot_data.filter(regex='^percentile',axis=1)

        if not focus_year:
            focus_year = matplot_data.index.year.max()

        elements_color = '#262626'
        fig, ax = plt.subplots(figsize=(22,17),facecolor='#ffffff')

        legend_list = []

        plt.grid(which='major', color='#666666', linestyle='-', alpha=0.1)
        plt.minorticks_on()
        plt.grid(which='minor', color='#999999', linestyle='-', alpha=0.05)
        
        plt.xticks(fontsize=20,color=elements_color)
        plt.yticks(fontsize=20,color=elements_color)

        ax.set_ylabel("Hauteur d'eau à la station piezométrique en m",size=25,color=elements_color)

        ax.spines['bottom'].set_color(elements_color)
        ax.spines['top'].set_color(elements_color)
        ax.spines['right'].set_color(elements_color)
        ax.spines['left'].set_color(elements_color)
        ax.set_xlim(1,365)

        ax.set_title(title,size=30,color=elements_color)

        last_date = matplot_data.index.max()
        txt = 'Dernière Mesure:\n' + '        '+ str(last_date)[:10]
        ax.annotate(txt, (0.92, 0.01),fontsize=12,xycoords='axes fraction',rotation=0,color=elements_color)

        y_label_pos = ax.get_yticks()[1:-2]
        y_label_name_reformat = []
        
        day_index = np.linspace(1,365,365)

        for percentile in percentile_extract.columns:
            try:
                plt.plot(day_index,matplot_data[matplot_data.index.year==focus_year][percentile].values,color=color_label[percentile],linewidth = 2.5, alpha=0.8) 
            except:
                plt.plot(day_index,matplot_data[matplot_data.index.year==focus_year][percentile].values,linewidth = 2.5, alpha=0.8) 
            legend_list.append(percentile)

        if past_year_number:
            if past_year_number != 1:
                year_list = np.linspace(focus_year-past_year_number,focus_year-1,past_year_number,dtype=int)
            else:
                year_list = [focus_year-1]
            for i,year in enumerate(year_list):
                color_list = get_color_gradient_hex(hex_color_start=gradient_color_past_year_start, hex_color_end=gradient_color_past_year_end, color_number=len(year_list))
                try:
                    plt.plot(day_index,matplot_data[matplot_data.index.year==year]['niveau_nappe_eau'].values,label=str(year),color=color_list[i],linewidth = 5,alpha=0.75,linestyle=':')
                    legend_list.append("Hauteur à la station piezo : " + str(year))
                except:
                    pass
        
        plt.plot(day_index,matplot_data[matplot_data.index.year==focus_year]['niveau_nappe_eau'].values,color='#000000',label=str(focus_year),linewidth = 5, alpha=1)
        legend_list.append("Hauteur à la station piezo : " + str(focus_year))

        if thresold:
            thresold_keys = list(thresold.keys())
            for key in thresold_keys:
                if thresold[key]:
                    plt.plot(day_index,thresold[key]*np.ones(365),color=color_label[key],linewidth = 3,in_layout=False,alpha=0.9,linestyle='--')
                    legend_list.append(key[6:])
                

        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.1f}'))

        y_label_pos = ax.get_yticks()[1:-2]
        
        y_label_name_reformat = []
        
        for i in range(len(y_label_pos)):
            if int(y_label_pos[i])==0:
                y_label_name_reformat.append(str(y_label_pos[i]).replace('.',','))
            else:
                y_label_name_reformat.append(str(int(y_label_pos[i])))
        
        ax.set_yticks(y_label_pos)
        ax.set_yticklabels(y_label_name_reformat) 

        month_list = ['Jan.','Fév.','Mars','Avril','Mai','Juin',
                      'Juil.','Aout','Sept.','Oct.','Nov.','Déc.']

        for month_line in [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]:
            plt.axvline(x=month_line, color="#666666",linewidth = 2,in_layout=False,alpha=0.5)

        ax.set_xticks([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334])
        ax.set_xticklabels(month_list,rotation=45)


        box = ax.get_position()
        ax.set_position([box.x0-0.05, box.y0+0.04, box.width*1.1, box.height])

        for i,label in enumerate(legend_list):
            try:
                legend_list[i] = relabel[label]
            except:
                pass

        ax.legend(legend_list, prop={'size': 15},loc='upper center',
                  bbox_to_anchor=(0.5, -0.08),
                  shadow=True,ncol=6)

        if save_fig:
            fig_path = save_path + save_name + '.png'
            try:
                os.makedirs(save_path)
            except:
                pass
            plt.savefig(fig_path, bbox_inches='tight')

        if show:
            plt.show()
        else:
            plt.close(fig)