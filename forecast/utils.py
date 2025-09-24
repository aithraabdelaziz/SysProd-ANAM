
from collections import defaultdict
from django.apps import apps
from datetime import datetime, date, timedelta
import locale
import os
from collections import OrderedDict
from chartmet.utils import generate_observation_map, generate_forecast_map, generate_model_map

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

def format_periode(display_periode,ech,date_bult):
    date_bult = datetime.combine(date_bult, datetime.min.time())
    if not display_periode :
        return ""
    emax = max([ h.start for h in ech]+[ h.end for h in ech])
    emin = min([ h.start for h in ech]+[ h.end for h in ech])
    d1 = date_bult + timedelta(hours=emin)
    d2 = date_bult + timedelta(hours=emax)
    periode = ""
    if (d2-d1) >= timedelta(days=2):
        if d1.strftime("%B") == d2.strftime("%B") :
            periode = d1.strftime("%A %d") + " au "+d2.strftime("%A %d %B %Y")
        else :
            periode = d1.strftime("%A %d %B") + " au "+d2.strftime("%A %d %B %Y")
    else :
        if d1.strftime("%B") == d2.strftime("%B") :
            periode = "du "+d1.strftime("%A %d à %Hh") + " au "+d2.strftime("%A %d %B %Y à %Hh")
        else :
            periode = "du "+d1.strftime("%A %d %B à %Hh") + " au "+d2.strftime("%A %d %B %Y à %Hh")
    return periode

def generate_echeances_dict(date_bult, echeances):
   
    # Dictionnaire pour stocker les résultats
    date_echeances_dict = {}

    # Variable pour suivre le jour d'ajout
    current_date = date_bult

    # Boucle pour remplir le dictionnaire
    for ech in echeances :
        # if isinstance(ech.echeance,int) : 
        #     current_date = date_bult + timedelta(hours=(ech.echeance-1))
        # if current_date not in date_echeances_dict:
        #     date_echeances_dict[current_date]={}
        try :
            echint = int(ech.echeance)
            current_date = date_bult + timedelta(hours=(echint-1))
        except :
            pass
        if current_date not in date_echeances_dict:
            date_echeances_dict[current_date]={}
        date_echeances_dict[current_date][ech.echeance]=ech.name

    return date_echeances_dict


def get_configured_elements_for_bulletin(bulletin):

    stations = set()
    zones = set()
    parametres = set()
    echeances = set()
    heures  = set()

    zone = set()
    parametre = set()
    echeance = set()

    obsmap = set()
    fcstmap = set()
    modelmap = set()

    result = {}
    for block in bulletin.content:
        value = block.value

        if hasattr(value, 'get'):
            if 'stations' in value:
                stations.update(value['stations'].stations.all())  # Localites de stations
            if 'zone' in value:
                zone.add(value['zone'])  # Station ou Zone
            if 'zones' in value:
                zones.update(value['zones'].villes.all())  # Localites
            if 'parametre' in value:
                parametre.add(value['parametre'])  # Variable
            if 'parametres' in value:
                parametres.update(value['parametres'].parametres.all())  # Parametres
            if 'echeance' in value:
                echeance.add(value['echeance'])  # Echeance
            if 'echeances' in value:
                echeances.update(value['echeances'].echeances.all())  # Echeances
            if 'heures' in value:
                heures.update(value['heures'].echeances.all())  # Heures

            if 'obsmap' in value:
                obsmap = value['obsmap'].id
            if 'fcstmap' in value:
                fcstmap = value['fcstmap'].id
            if 'modelmap' in value:
                modelmap = value['modelmap'].id

    
    result = {
        'stations': list(stations),
        'villes': list(zones),
        'parametres': list(parametres),
        'echeances': list(echeances),
        'heures': list(heures),
        'zone': list(zone),
        'parametre': list(parametre),
        'echeance': list(echeance),
        'obsmap': (obsmap),
        'fcstmap': (fcstmap),
        'modelmap': (modelmap),
    }

    return result



