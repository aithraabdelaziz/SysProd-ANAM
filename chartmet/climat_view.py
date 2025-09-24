from django.shortcuts import render, redirect, get_object_or_404
from collections import defaultdict
from observation.models import ClimatMois, ClimatDecades
from .models import MapModelConfiguration
from .utils import generate_ClimMonth_map, generate_Decadaire_map
from .constantes import *
from datetime import date
from pprint import pprint

def index_climat(request):
    return render(request, 'climat/index.html')
def list_cartes(request):
    return render(request, 'climat/liste_cartes.html')
def imports(request):
    return render(request, 'climat/imports.html')

def month_map_form(request):
    entries = ClimatMois.objects.values('source', 'parameter', 'name').distinct()
    sources = defaultdict(list)
    for entry in entries:
        source = entry['source'] or 'Inconnu'  # gérer les sources nulles si besoin
        param_name = {entry['parameter']: entry['name']}
        if param_name not in sources[source]:
            sources[source].append(param_name)
    sources = dict(sources)

    functions = [
        {"name": "Moyenne","function":"mean"},
        {"name": "Cumul","function": "sum"},
        {"name": "Maximum","function":   "max"},
        {"name": "Minimum","function":   "min"},
        {"name": "Somme","function": "sum"}
    ]
    MapConfig = MapModelConfiguration.objects.filter(active=True)


    context={"sources_params":sources,'functions': functions,'maps':MapConfig}
    return render(request, 'climat/map_month_form.html',context)

def generate_monthly_clim_map(request):
    if request.method == 'POST':
        from_date = request.POST.get('from')        # format YYYY-MM
        to_date = request.POST.get('to')            # format YYYY-MM
        param = request.POST.get('parametre')       # code paramètre sélectionné (ex: 'tp')
        source = request.POST.get('source')         # source sélectionnée (ex: 'ecmf')
        function = request.POST.get('function')     # fonction sélectionnée
        confMap_id = request.POST.get('mapModel')   # ID du template de carte sélectionné

        # Séparation année/mois 
        from_year, from_month = map(int, from_date.split('-'))
        to_year, to_month = map(int, to_date.split('-'))
        if confMap_id=="0" : confMap_id=None

        context = generate_ClimMonth_map(from_year, from_month,to_year,to_month,param,source=source,function=function,pk=confMap_id)
        pprint(context)
        print('----------------')
        return render(request, 'climat/map_show.html', context)
    return render(request, 'climat/map_show.html', {})

FUNCTIONS = [
        {"name": "Ecart","function":"diff"},
        {"name": "Moyenne","function":"mean"},
        {"name": "Cumul","function": "sum"},
        {"name": "Maximum","function":   "max"},
        {"name": "Minimum","function":   "min"},
        {"name": "Somme","function": "sum"}
    ]
def decade_map_form(request):
    entries = ClimatDecades.objects.values('source', 'parameter').distinct()
    sources = defaultdict(list)

    for entry in entries:
        source = entry['source'] or 'Inconnu'  # gérer les sources nulles si besoin
        param_name = {entry['parameter']: entry['parameter']}
        if param_name not in sources[source]:
            sources[source].append(param_name)
    sources = dict(sources)

    MapConfig = MapModelConfiguration.objects.filter(active=True)


    context={'today': date.today(),"sources_params":sources,'functions': FUNCTIONS,'maps':MapConfig,'inertpolation':INERTPOLATIONS,'extrapolation':EXTRAPOLATIONS,'variogramme':VARIOGRAMS}
    return render(request, 'climat/map_decade_form.html',context)

def generate_decade_clim_map(request):
    if request.method == 'POST':
        try:
            date_string = request.POST.get('date')               # Format : 'YYYY-MM-DD'
            decade1 = int(request.POST.get('decade1'))-1           # Offset : -1, 0, 1 # on soustrait 1 car le bulletin est élaboré à la décade suivante de celle du bulletin
            decade2 = int(request.POST.get('decade2'))-1           # Offset : -1, 0, 1 # donc la décade courante est la décade du bulletin (donc -1)
            source = request.POST.get('source')
            param = request.POST.get('parametre')
            fonction = request.POST.get('function')
            interpolation = request.POST.get('interpolation')
            extrapolation = request.POST.get('extrapolation')
            variogramme = request.POST.get('variogramme')
            nugget = request.POST.get('nugget')
            range_ = request.POST.get('range')
            sill = request.POST.get('sill')
            confMap_id = request.POST.get('mapModel')

            if nugget!="" and range_!="" and sill!="" :
                param_variogramme = {'nugget':float(nugget),'range':float(range_),'sill':float(sill)}
            else :
                param_variogramme=""
            func_name = next((f["name"] for f in FUNCTIONS if f["function"] == fonction), '')
            confMap = None
            if confMap_id and confMap_id != "0":
                confMap = MapModelConfiguration.objects.get(pk=confMap_id)
            context = generate_Decadaire_map(
                date_string=date_string,
                decade1=decade1,
                decade2=decade2,
                source=source,
                parametre=param,
                fonction=fonction,
                func_name = func_name,
                pk=confMap.id,
                interpolation=interpolation,
                extrapolation=extrapolation,
                variogramme=variogramme,
                param_variogramme = param_variogramme
            )


            print("Carte décadaire générée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la génération : {str(e)}")
            context = {}
    return render(request, 'climat/map_show.html', context)

