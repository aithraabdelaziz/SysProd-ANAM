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
############# Views for Stations####################@
##################################################@
from observation.models import Station
class StationListView(ListView):
    model = Station
    template_name = 'stations/station_list.html'
    context_object_name = 'areas'  # Nom de la variable passée au template
    paginate_by = 15  # Nombre d'éléments par page
    def get_queryset(self):
        queryset = super().get_queryset()

        # Get parameters from the request
        wigos_id = self.request.GET.get('wigos_id', None)
        active = self.request.GET.get('active', None)
        inactive = self.request.GET.get('inactive', None)
        search_query = self.request.GET.get('search', '')
        # Apply filters based on parameters
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        if wigos_id:
            queryset = queryset.filter(wigos_id=wigos_id)
        if active is not None:
            #active = active.lower() == 'true'
            queryset = queryset.filter(active='True')
        if inactive is not None:
            #inactive = inactive.lower() == 'false'
            queryset = queryset.filter(active='False')

        queryset = queryset.order_by('name')

        return queryset

class StationCreateView(CreateView):
    model = Station
    template_name = 'stations/station_form.html'
    fields = ['name', 'geom','active','wigos_id']
    success_url = reverse_lazy('observation:station_list')

    def form_valid(self, form):
        # Récupérez la géométrie à partir des données du formulaire
        geom_wkt = self.request.POST.get('geom')
        geom_geos = GEOSGeometry(geom_wkt)

        # Créez une instance du modèle avec la géométrie et sauvegardez-la
        instance = form.save(commit=False)
        instance.geom = geom_geos
        instance.save()

        return super().form_valid(form)

class StationUpdateView(UpdateView):
    model = Station
    template_name = 'stations/station_form.html'
    fields = ['name', 'geom','active','wigos_id']
    success_url = reverse_lazy('observation:station_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Convertir la géométrie GEOS en WKT
        #context['geom_wkt'] = self.object.geom.wkt if self.object.geom else None
        # print("#########geom wkt #########",self.object.geom.wkt)
        # print("#########geom#########",self.object.geom)
        context['geom_wkt'] = self.object.geom.wkt if self.object.geom else None
        return context

    def form_valid(self, form):
        # Récupérez la géométrie à partir des données du formulaire
        geom_wkt = self.request.POST.get('geom')
        geom_geos = GEOSGeometry(geom_wkt)

        # Créez une instance du modèle avec la géométrie et sauvegardez-la
        instance = form.save(commit=False)
        instance.geom = geom_geos
        instance.save()

        return super().form_valid(form)

class StationDeleteView(DeleteView):
    model = Station
    template_name = 'stations/station_confirm_delete.html'
    success_url = reverse_lazy('observation:station_list')

class StationDeactivateView(View):
    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(Station, pk=self.kwargs['pk'])
        if obj.active == True: obj.active=False
        else : obj.active=True
        obj.save()
        return redirect('observation:station_list')

class SelectStationsView(View):
    template_name = 'stations/select_station.html'

    #def get(self, request):
        # Récupérer toutes les instances du modèle
        # georaphic_areas = Zone.objects.all()
        # return render(request, self.template_name, {'georaphic_areas': georaphic_areas})

    def get(self, request):
        # Récupérer toutes les instances du modèle
        stations = Station.objects.all()

        # Filtrer par catégorie
        wigos_id_filter = request.GET.get('wigos_id')
        if wigos_id_filter:
            stations = stations.filter(wigos_id=wigos_id_filter)

        # Filtrer par statut (active/inactive)
        active_filter = request.GET.get('active')
        if active_filter:
            stations = stations.filter(active=True)
        else:
            inactive_filter = request.GET.get('inactive')
            if inactive_filter:
                stations = stations.filter(active=False)

        return render(request, self.template_name, {'stations': stations})

def shapefile_station_view(request):
    attribut_columns = []  # Initialisez la liste des attributs à afficher

    shapefile=None
    if request.method == 'POST':
        if request.POST.get('action') == 'upload':
            form = ShapefileUploadForm(request.POST, request.FILES)

            try:
            # if True :
                if form.is_valid():
                    shapefile = request.FILES['shapefile']
                    file_name = shapefile.name
                    temp_file_path = default_storage.save(file_name, ContentFile(shapefile.read()))
            
                    if shapefile.content_type == 'application/zip' or shapefile.content_type == 'application/x-zip-compressed':
                        zip_file_path = default_storage.path(temp_file_path)
                        gdf = gpd.read_file(f"zip://{zip_file_path}")
                        # gdf = gpd.read_file(f"zip://{shapefile.name}")
                    else:
                        #print("######shape",request.session['shapefile_path'])
                        gdf = gpd.read_file(shapefile.temporary_file_path())
                    # Save the GeoDataFrame to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                        gdf.to_file(tmp_file.name, driver='GeoJSON')
                        request.session['gdf_file_path'] = tmp_file.name
                        
                    attribut_columns = gdf.columns.tolist()

            except Exception as e:
                # Gérer les exceptions liées au téléchargement du fichier
                form.add_error('shapefile', f"Erreur lors du téléchargement du fichier .Veuillez vérifier le format du fichier.")
                # messages.error(request, f"Une erreur de téléchargement s'est produite : {str(e)}")
            

        elif request.POST.get('action') == 'save':
             #####################

            #form = ShapefileUploadForm(request.POST, request.FILES)
            shapefile = request.FILES.get('shapefile')
            selected_attribute = request.POST.get('selected_attribute')
            selected_wigos=request.POST.get('selected_wigos')

            # print("##################path",shapefile)
            # gdf = gpd.read_file(shapefile.temporary_file_path())
            gdf_file_path = request.session.get('gdf_file_path')
            if gdf_file_path:
                gdf = gpd.read_file(gdf_file_path)

             # Créer une instance de GeographicArea pour chaque forme
            for index, row in gdf.iterrows():
                if selected_attribute != "aucun":
                    stat = Station.objects.create(
                    name=row[selected_attribute],
                    geom=GEOSGeometry(dumps(row['geometry'])),
                    active=True,
                    wigos_id=selected_wigos
                )
                else :
                    characters = string.ascii_letters + string.digits
                    selected_attribute = "Station_"+''.join(random.choice(characters) for _ in range(4))
                    stat = Station.objects.create(
                        name=selected_attribute,
                        #geom=row['geometry'],
                        geom=GEOSGeometry(dumps(row['geometry'])),
                        active = True,
                        wigos_id=selected_wigos
                    )
                    stat.save()

            # print("###########instance creé#############")
            return redirect('observation:station_list')

            ######################
    else:
        form = ShapefileUploadForm()

    return render(request, 'stations/shapefile.html', {'form': form, 'attribut_columns': attribut_columns,'shapefile':shapefile})

def save_station(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        shapefile = request.FILES.get('shapefile')

        #shapefile_path = request.session.get('shapefile_path', None)

        selected_attribute = request.POST.get('selected_attribute')
        selected_wigos=request.POST.get('selected_wigos')
        # print("###########",shapefile,"##########",selected_attribute,"#########",selected_category)
        #path_without_vsizip = shapefile_path.replace('/vsizip/', '')
        # print("##################path",shapefile)
        gdf = gpd.read_file(shapefile.temporary_file_path())

        # Créer une instance de GeographicArea pour chaque forme
        for index, row in gdf.iterrows():
            stat = Station.objects.create(
                name=row[selected_attribute],  # Vous pouvez utiliser row[selected_attribute] ou d'autres champs selon vos besoins
                geom=row['geometry'],  # Assurez-vous que le nom de la colonne de géométrie est correct
                active = True,
                wigos_id=selected_wigos
            )
            stat.save()

        
    return redirect('observation:station_list')
