
from pyhubeau import RequestDataHubeau, SiteHydroApp
from ddtoolkit import  HydroTool

ht = HydroTool()

RDH = RequestDataHubeau()
SHA = SiteHydroApp()

for i, site_hydro_id in enumerate(ht.site_hydro_list):
    site_hydro_table = RDH.get_hydro_obs_elab(site_hydro_id)
    site_hdyro_data, month_percentile = SHA.gen_site_hydro_data_based_on_all(site_hydro_table)
    graph_site_data = SHA.gen_graph_site_data(site_hdyro_data, month_percentile).drop(columns=["libelle_statut","libelle_methode","libelle_qualification"])

    SHA.matplot_graph_generation(graph_site_data/1000,
                                past_year_number=4,
                                title=ht.site_hydro_options[site_hydro_id]['title'],
                                color_label=ht.color_label,
                                relabel=ht.relabel,
                                thresold=ht.site_hydro_options[site_hydro_id]['thresold'],
                                show=False,
                                save_fig=True,
                                save_path="hydro\\graph_site_hydro\\",
                                save_name=f'{i:05}')