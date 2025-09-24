from django.shortcuts import render

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required, login_required, permission_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

CLASS_NUMBER = 101
from django.template.defaulttags import register
from django.urls import reverse_lazy
# from django.http import HttpResponse
from django.views import View
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
# from django.core.exceptions import ValidationError

from django.shortcuts import redirect
import geopandas as gpd
from observation.forms import ShapefileUploadForm
from shapely.wkt import dumps
from django.core.serializers import serialize
import json

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile 
import os


import tempfile
import random
import string

from django.shortcuts import render, get_object_or_404, redirect
from forecast.models import Variable
from observation.models import Station,Observation
from bulletins.models import Localites,Echeances, BulletinTemplate, Echeance, Parametres
from forecast.forms import ForecastForm
from django.utils.dateparse import parse_date
from django.contrib import messages
from pprint import pprint

from meteowise.symbols_select import generer_select_icones_weather,render_weather_icon_select

from datetime import datetime

from django.urls import reverse


def unique_object(objects):
    seen = set()
    result = []
    for obj in objects:
        if obj.id not in seen:
            seen.add(obj.id)
            result.append(obj)
    return result

def index(request): 
    
    return render(request, 'observation/editions/index.html')


def select_localite(request):
    localites = Localites.objects.all()
    return render(request, 'observation/editions/select_localite.html', {'localites': localites})

def select_station(request, localite_id):
    print('----------')
    localite = get_object_or_404(Localites, pk=localite_id)
    stations = localite.stations.all()
    zone = localite.zone
    stations = [ s for s in stations]
    stations.append(zone)
    return render(request, 'observation/editions/select_station.html', {'localite': localite, 'stations': stations})

def select_date(request, localite_id, zone_id):
    localite = get_object_or_404(Localites, pk=localite_id)
    echeancesGroup = Echeances.objects.all()
    echeances=[]
    for ge in echeancesGroup :
        echeances+=list(ge.echeances.all())
    echeances = unique_object(echeances)
    return render(request, 'observation/editions/select_date.html', {
        'localite_id': localite_id,
        'zone_id': zone_id,
        'echeances': echeances,
        'date' : datetime.now().strftime('%Y-%m-%d')
    })

def edit_observation(request):

    if request.method == 'POST':
        localite_id = int(request.POST.get('localite'))
        localite = get_object_or_404(Localites, pk=localite_id)
        station_id = int(request.POST.get('zone'))
        station = get_object_or_404(Station, pk=station_id)
        date_str = request.POST.get('date')
        heure = request.POST.get('echeance')
    else :
        return render(request, 'observation/editions/edit_observations.html', {})

    parametersGroup = Parametres.objects.all()
    parameters=[]
    for gp in parametersGroup :
        parameters+=list(gp.parametres.all())
    parameters = unique_object(parameters)
    

    observations = []
    select_html={}

    for param in parameters:
        obs, _ = Observation.objects.get_or_create(
            station=station,
            date=date_str,
            parametre=param,
            heure=heure
        )
        if param.shortName== 'symbol_code':
            select_html = render_weather_icon_select(selected=obs.observation)
        observations.append(obs)
    if request.method == 'POST':
        saved = False
        for observation in observations:
            field_name = f"value_{observation.parametre.id}"
            if field_name in request.POST:
                saved = True
                observation.observation = request.POST.get(field_name)
                observation.save()
        if saved :
            messages.success(request, "Observation mises à jour avec succès.")
            url = reverse("observation:select_station", args=[localite_id])
            return redirect(url)
    context = {
        'localite': localite,
        'station': station,
        'date_aff': datetime.strptime(date_str, "%Y-%m-%d").date(),
        'date': date_str,
        'heure': heure,
        'observations': observations,
        "weather_select": select_html
    }
    return render(request, 'observation/editions/edit_observations.html', context)