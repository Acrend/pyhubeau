<h1>pyhubeau : Simplification de l'usage de l'API Hubeau avec Python</h1>

<h3>Introduction</h3>

L'application pyhubeau vise à simplifier l'utilisation de l'API Hubeau (https://hubeau.eaufrance.fr/) en Python. Actuellement, elle se présente sous la forme d'un script simple à importer dans votre projet. Ce projet représente ma première incursion dans le monde open source et Git. Je maintiens cette application principalement pour faciliter mon usage personnel de l'API Hubeau. Je ne suis pas un expert en programmation et je suis encore en apprentissage des subtilités du domaine. Mon objectif est d'améliorer constamment pyhubeau, avec l'ambition de peut-être supporter intégralement Hubeau v1 à l'avenir. Tous les retours constructifs sont bienvenus !

<h3>Fonctionnalités Actuelles</h3>

Les fonctionnalités les plus avancées de l'application incluent l'exploitation des données piézométriques et hydrométriques (débit).


<h3>Utilisation</h3>

Pour utiliser pyhubeau, vous pouvez consulter les scripts **hydro_v3.py** et **piezo_v3.py**. Ils ne contiennent pas encore de commentaires, mais des ajouts explicatifs sont prévus prochainement.

<h3>Exemples d'Utilisation</h3>


```python
from pyhubeau import RequestDataHubeau

rdh = RequestDataHubeau()

site_hydro_id = "K6022420"
station_piezo_id = "04936X0010/f"

station_piezo_data = rdh.get_station_piezo_chroniques(station_piezo_id)
site_hydro_data = rdh.get_hydro_obs_elab(site_hydro_id)
```

Pour obtenir la liste des sites hydrologiques et stations piézométriques :

```python
from pyhubeau import RequestDataHubeau

rdh = RequestDataHubeau()

site_hydro_info = rdh.get_site_hydro_info()
station_piezo_info = rdh.get_station_piezo()
```
