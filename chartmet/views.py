from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import MultipleObjectsReturned

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')  # Pas de GUI
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from django.contrib.staticfiles import finders
from PIL import Image
from django.conf import settings
import os
from wagtail.api.v2.utils import get_full_url
from forecast.models import Forecast, Zone,Variable
from observation.models import Observation,Station
from datetime import date

from django.conf import settings
import folium
from folium.plugins import MarkerCluster
from folium.features import CustomIcon
import locale

from datetime import datetime, timedelta
from pprint import pprint
from django.shortcuts import render
from django.http import Http404
import os
from datetime import datetime
from django.conf import settings
from django.contrib.gis.geos import Point

from .models import * 
from bs4 import BeautifulSoup

from .utils import generate_observation_map, generate_forecast_map, generate_model_map, get_parameters, get_functions
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


def index(request):
    return render(request, 'index.html')

def sensitive_map_form(request):
    distinct_dates_echeances = Forecast.objects.filter(zone__category='ville') \
        .values('date', 'echeance') \
        .distinct()
    # Organiser les données par date (et les échéances pour chaque date)
    dates_echeances = {}
    for item in distinct_dates_echeances:
        date_str = item['date'].isoformat()  # 'YYYY-MM-DD'
        if date_str not in dates_echeances:
            dates_echeances[date_str] = []
        dates_echeances[date_str].append(item['echeance'])
    MapConfig = MapFcstConfiguration.objects.filter(active=True)
    return render(request, 'sensitivemap/sensitive_map_form.html',{
        'dates_echeances': dates_echeances,'maps':MapConfig
    })

def sensitive_map_show(request):
    date_str = request.GET.get('date')
    echeance = request.GET.get('echeance')

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.strftime('%Y')
        month = date_obj.strftime('%m')
        day = date_obj.strftime('%d')
    except ValueError:
        raise Http404("Date invalide")

    image_path = f'media/carte_prevision/{year}/{month}/{day}/{echeance}/img.png'
    full_path = os.path.join(settings.BASE_DIR, image_path)

    if not os.path.exists(full_path):
        raise Http404("Carte non trouvée")

    context = {
        'image_url': f'/{image_path}',
        'date': date_str,
        'echeance': echeance,
    }
    return render(request, 'sensitivemap/sensitive_map_show.html', context)


def generate_map(request):
    if request.method == 'POST':
        date_string = request.POST.get('date')
        echeance = request.POST.get('echeance')
        mapid = request.POST.get('map')
        if mapid=="0" : mapid=None
        context = generate_forecast_map(date_string, echeance,mapid)
        return render(request, 'map.html', context)
    return render(request, 'map.html', {})

###############################################
######   OBSERVATION    #######################
###############################################

def obs_index(request):
    return render(request, 'obs_index.html')

def sensitive_obsmap_form(request):
    distinct_dates_echeances = Observation.objects.filter(heure='9 last 24h') \
        .values('date', 'heure') \
        .distinct()
    stations = Station.objects.all()

    distinct_dates_echeances = Observation.objects.filter(station__in = stations) \
        .values('date', 'heure') \
        .distinct()
    # Organiser les données par date (et les échéances pour chaque date)
    dates_echeances = {}
    for item in distinct_dates_echeances:
        date_str = item['date'].isoformat()  # 'YYYY-MM-DD'
        if date_str not in dates_echeances:
            dates_echeances[date_str] = []
        dates_echeances[date_str].append(item['heure'])
    MapConfig = MapObsConfiguration.objects.filter(active=True)
    return render(request, 'sensitivemap/sensitive_obsmap_form.html',{
        'dates_echeances': dates_echeances,'maps':MapConfig
    })

def sensitive_obsmap_show(request):
    date_str = request.GET.get('date')
    echeance = request.GET.get('heure')
    echeance = request.GET.get('map')

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.strftime('%Y')
        month = date_obj.strftime('%m')
        day = date_obj.strftime('%d')
    except ValueError:
        raise Http404("Date invalide")

    image_path = f'media/carte_observation/{year}/{month}/{day}/{echeance}/img.png'
    full_path = os.path.join(settings.BASE_DIR, image_path)

    if not os.path.exists(full_path):
        raise Http404("Carte non trouvée")

    context = {
        'image_url': f'/{image_path}',
        'date': date_str,
        'echeance': echeance,
    }
    return render(request, 'sensitivemap/sensitive_obsmap_show.html', context)

def generate_obsmap(request):
    if request.method == 'POST':
        date_string = request.POST.get('date')
        heure = request.POST.get('heure')
        mapid = request.POST.get('map')
        if mapid=="0" : mapid=None
        context = generate_observation_map(date_string, heure,mapid)
        return render(request, 'map_obs.html', context)
    return render(request, 'map_obs.html', {})

def model_map_form(request):

    model = {'name':'GFS','schema':'gfs_model'}

    parametres = get_parameters(schema='gfs_model').to_dict(orient='records')
    functions = get_functions(schema='gfs_model').to_dict(orient='records')
    MapConfig = MapModelConfiguration.objects.filter(active=True)


    context = {'parametres': parametres,'functions': functions,'maps':MapConfig}

    return render(request, 'modelmap/map_form.html',context)

def generate_modelmap(request):
    if request.method == 'POST':
        date_string = request.POST.get('date')
        ech1 = request.POST.get('echeance1')
        ech2 = request.POST.get('echeance2')
        param = request.POST.get('parametre')
        function = request.POST.get('function')
        confMap_id = request.POST.get('mapModel')
        if confMap_id=="0" : confMap_id=None
        context = generate_model_map(date_string, ech1,ech2,param,function=function,pk=confMap_id,schema='gfs_model',table='weather_data')
        # context = generate_model_map(date_string, ech1,ech2,param,function,confMap)
        return render(request, 'model_map.html', context)
    return render(request, 'model_map.html', {})

from django.http import HttpResponse
from bulletins.models import Localites,Echeance
from .utils import generate_points_map
def extrapolated_map_form(request):
    
    parametres = Variable.objects.filter(active=True)
    echeances = Echeance.objects.filter(active=True)
    localites = Localites.objects.all()
    functions = get_functions(schema='gfs_model').to_dict(orient='records')
    MapConfig = MapModelConfiguration.objects.filter(active=True)


    context = {'parametres': parametres,'echeances': echeances,'localites':localites,'maps':MapConfig}

    return render(request, 'points_map/points_map_form.html',context)
def points_map(request):
    if request.method == 'POST':
        date_string = request.POST.get('date')
        ech_id = request.POST.get('echeance')
        param_id = request.POST.get('parametre')
        source = request.POST.get('source')
        loc_id = request.POST.get('localites')
        confMap_id = request.POST.get('mapModel')
        if confMap_id=="0" : confMap_id=None
        
        param = Variable.objects.get(pk=param_id)
        localite = Localites.objects.get(pk=loc_id)
        echeance = Echeance.objects.get(pk=ech_id)
   
        context = generate_points_map(date_string,localite,param,echeance,pk=confMap_id)
        return render(request, 'points_map/map_show.html', context)
    return render(request, 'points_map/map_show.html', {})


def extrapolated_mapPreconfigured_form(request):
    
    localites = Localites.objects.all()

    MapConfig = MapSpatialConfiguration.objects.filter(active=True)


    context = {'localites':localites,'maps':MapConfig}

    return render(request, 'points_map/points_spatial_map_form.html',context)


from .utils import generate_Spatial_points_map
def points_map_preconfigured(request):
    if request.method == 'POST':
        date_string = request.POST.get('date')
        
        source = request.POST.get('source')
        loc_id = request.POST.get('localites')
        confMap_id = request.POST.get('mapModel')
        if confMap_id=="0" : confMap_id=None
        
       
        localite = Localites.objects.get(pk=loc_id)
   
        # context = generate_points_map(date_string,localite,param,echeance,pk=confMap_id)
        context = generate_Spatial_points_map(date_string,localite,pk=confMap_id)
        return render(request, 'points_map/map_show.html', context)
    return render(request, 'points_map/map_show.html', {})
