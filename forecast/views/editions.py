from django.shortcuts import render, get_object_or_404, redirect
from forecast.models import Forecast, Zone, Variable
from bulletins.models import Localites,Echeances, BulletinTemplate, Echeance, Parametres
from forecast.forms import ForecastForm
from django.utils.dateparse import parse_date
from django.contrib import messages
from pprint import pprint
from meteowise.symbols_select import generer_select_icones_weather,render_weather_icon_select

from  forecast.models import Zone,Variable
from observation.models import Station
from forecast.utils import get_configured_elements_for_bulletin

from datetime import datetime
from django.urls import reverse
from django.contrib.auth.decorators import permission_required

def unique_object(objects):
    seen = set()
    result = []
    for obj in objects:
        if obj.id not in seen:
            seen.add(obj.id)
            result.append(obj)
    return result

def index(request):
    
    return render(request, 'forecast/editions/index.html')

@permission_required('forecast.edit_forecast', raise_exception=True)
def select_bulletins(request):
    bulletins = BulletinTemplate.objects.filter(active=True)
    return render(request, 'forecast/editions_bulletins/select_bulletins.html', {'bulletins': bulletins})
@permission_required('forecast.edit_forecast', raise_exception=True)
def select_zonebulletin(request, bulletin_id):
    bulletin = get_object_or_404(BulletinTemplate, pk=bulletin_id)
    elmts = get_configured_elements_for_bulletin(bulletin)
    zones_obs=[]
    zones_fcst=[]
    stations = []
    villes = []

    for z in elmts['zone'] :
        if isinstance(z,Station) : zones_obs.append(z)
        if isinstance(z,Station) : zones_fcst.append(z)
    for z in elmts['zone'] :
        if isinstance(z,Station) : zones_obs.append(z)
        if isinstance(z,Station) : zones_fcst.append(z)

    print(f'------{bulletin.name}-----')
    pprint(zones_fcst)
    return render(request, 'forecast/editions_bulletins/select_zone.html', {'localite': bulletin,'blocks':elmts})


@permission_required('forecast.edit_forecast', raise_exception=True)
def select_localites(request):
    localites = Localites.objects.all()
    return render(request, 'forecast/editions/select_localites.html', {'localites': localites})
@permission_required('forecast.edit_forecast', raise_exception=True)
def select_zone(request, localite_id):
    localite = get_object_or_404(Localites, pk=localite_id)
    zones = localite.villes.all()
    zone = localite.zone
    zones = [z for z in zones]
    zones.append(zone)
    return render(request, 'forecast/editions/select_zone.html', {'localite': localite, 'zones': zones})
@permission_required('forecast.edit_forecast', raise_exception=True)
def select_date(request, localite_id, zone_id):
    localite = get_object_or_404(Localites, pk=localite_id)
    # echeancesGroup = Echeances.objects.all()
    # echeances=[]
    # for ge in echeancesGroup :
    #     echeances+=list(ge.echeances.all())
    # echeances = unique_object(echeances)
    echeances = Echeances.objects.get(name='forecasts').echeances.all()
    # echeances = Echeance.objects.all()
    # pprint(echeances)
    return render(request, 'forecast/editions/select_date.html', {
        'localite_id': localite_id,
        'zone_id': zone_id,
        'echeances': echeances,
        'date' : datetime.now().strftime('%Y-%m-%d')
    })
@permission_required('forecast.edit_forecast', raise_exception=True)
def edit_forecasts(request):

    if request.method == 'POST':
        localite_id = int(request.POST.get('localite'))
        localite = get_object_or_404(Localites, pk=localite_id)
        zone_id = int(request.POST.get('zone'))
        zone = get_object_or_404(Zone, pk=zone_id)
        date_str = request.POST.get('date')
        echeance = request.POST.get('echeance')
    else :
        return render(request, 'observation/editions/edit_observations.html', {})
    

    parametersGroup = Parametres.objects.all()
    parameters=[]
    for gp in parametersGroup :
        parameters+=list(gp.parametres.all())
    parameters = unique_object(parameters)
    forecasts = []
    select_html={}
    # date, echeance, id, observation, parametre, parametre_id, prevision, zone, zone_id
    for param in parameters:
        forecast, _ = Forecast.objects.get_or_create(
            zone=zone,
            date=date_str,
            parametre=param,
            echeance=echeance
        )
        if param.shortName== 'symbol_code':
            select_html = render_weather_icon_select(name=f'value_{forecast.parametre.id}',selected=forecast.prevision)
        forecasts.append(forecast)
    
    if request.method == 'POST':
        saved = False
        for forecast in forecasts:
            field_name = f"value_{forecast.parametre.id}"
            if field_name in request.POST:
                saved = True
                forecast.prevision = request.POST.get(field_name)
                forecast.save()
        if saved :
            messages.success(request, "Prévisions mises à jour avec succès.")
            url = reverse("forecast:select_zone", args=[localite_id])
            return redirect(url)

    return render(request, 'forecast/editions/edit_forecasts.html', {
        'localite': localite,
        'zone': zone,
        'date_aff': datetime.strptime(date_str, "%Y-%m-%d").date(),
        'date': date_str,
        'echeance': echeance,
        'forecasts': forecasts,
        "weather_select": select_html
    })
