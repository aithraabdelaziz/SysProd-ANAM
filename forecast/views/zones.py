from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required, login_required


CLASS_NUMBER = 101
from django.template.defaulttags import register
###########  Views for Zones #######################################
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from forecast.models import Zone

# from django.http import HttpResponse
from django.views import View
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
# from django.core.exceptions import ValidationError

import geopandas as gpd
from forecast.forms import ShapefileUploadForm,MergeZonesForm
from shapely.wkt import dumps
from django.core.serializers import serialize
import json

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile 
import os

from django.contrib.gis.geos import MultiPolygon,Polygon

import tempfile
import random
import string
from pprint import pprint
############# Views for Zones####################@
##################################################@
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView
class ZonePermission(PermissionRequiredMixin):
    permission_required = 'forecast.edit_zone'
    raise_exception = True

class ZoneListView(ZonePermission, ListView):
    model = Zone
    template_name = 'zones/georaphic_area_list.html'
    context_object_name = 'areas'  # Nom de la variable passée au template
    paginate_by = 15  # Nombre d'éléments par page

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get parameters from the request
        category = self.request.GET.get('category', None)
        active = self.request.GET.get('active', None)
        inactive = self.request.GET.get('inactive', None)
        search_query = self.request.GET.get('search', '')
        # Apply filters based on parameters
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        if category:
            queryset = queryset.filter(category=category)
        if active is not None:
            #active = active.lower() == 'true'
            queryset = queryset.filter(active='True')
        if inactive is not None:
            #inactive = inactive.lower() == 'false'
            queryset = queryset.filter(active='False')

        queryset = queryset.order_by('name')

        return queryset


class ZoneCreateView(ZonePermission, CreateView):
    model = Zone
    template_name = 'zones/georaphic_area_form.html'
    fields = ['name', 'geom','active','category','rayon']
    success_url = reverse_lazy('forecast:georaphic_area_list')

    def form_valid(self, form):
        # Récupérez la géométrie à partir des données du formulaire
        geom_wkt = self.request.POST.get('geom')
        geom_geos = GEOSGeometry(geom_wkt)

        # Créez une instance du modèle avec la géométrie et sauvegardez-la
        instance = form.save(commit=False)
        instance.geom = geom_geos
        instance.save()

        return super().form_valid(form)

class ZoneUpdateView(ZonePermission, UpdateView):
    model = Zone
    template_name = 'zones/georaphic_area_form.html'
    fields = ['name', 'geom','active','category','rayon']
    success_url = reverse_lazy('forecast:georaphic_area_list')

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

class ZoneDeleteView(ZonePermission, DeleteView):
    model = Zone
    template_name = 'zones/georaphic_area_confirm_delete.html'
    success_url = reverse_lazy('forecast:georaphic_area_list')

class ZoneDeactivateView(ZonePermission, View):
    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(Zone, pk=self.kwargs['pk'])
        if obj.active == True: obj.active=False
        else : obj.active=True
        obj.save()
        return redirect('forecast:georaphic_area_list')

class SelectZonesView(ZonePermission, View):
    template_name = 'zones/select_georaphic_areas.html'

    def get(self, request):
        # Récupérer toutes les instances du modèle
        georaphic_areas = Zone.objects.all().order_by('name')

        # Filtrer par catégorie
        category_filter = request.GET.get('category')
        if category_filter:
            georaphic_areas = georaphic_areas.filter(category=category_filter)

        # Filtrer par statut (active/inactive)
        active_filter = request.GET.get('active')
        if active_filter:
            georaphic_areas = georaphic_areas.filter(active=True)
        else:
            inactive_filter = request.GET.get('inactive')
            if inactive_filter:
                georaphic_areas = georaphic_areas.filter(active=False)

        return render(request, self.template_name, {'georaphic_areas': georaphic_areas})

class MergeZonesView(ZonePermission, View):
    template_name = 'zones/merge_georaphic_areas.html'

    def get(self, request):
        # Récupérer les IDs sélectionnés à partir des paramètres de requête
        selected_ids = request.GET.getlist('selected_ids')
        selected_idss = [int(id) for id in selected_ids]

        # Récupérer les instances sélectionnées
        selected_instances = Zone.objects.filter(pk__in=selected_ids)

        # Sérialiser les géométries sélectionnées en format JSON
        selected_geometries_json = serialize('geojson', selected_instances, geometry_field='geom')

        return render(request, self.template_name, {'selected_ids':selected_idss,'selected_geometries_json': selected_geometries_json})

        # # fusionner les géométries et effectuer d'autres opérations si nécessaire

        # return render(request, self.template_name, {'selected_instances': selected_instances})


def shapefile_view(request):
    attribut_columns = []  # Initialisez la liste des attributs à afficher

    category_choices = [choice[0] for choice in Zone.CATEGORY_CHOICES]
    selected_rayon = 0
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
            selected_category=request.POST.get('selected_category')
            selected_rayon=request.POST.get('rayon')
            print("###########",shapefile,"##########",selected_attribute,"#########",selected_category)

            # print("##################path",shapefile)
            # gdf = gpd.read_file(shapefile.temporary_file_path())
            gdf_file_path = request.session.get('gdf_file_path')
            if gdf_file_path:
                gdf = gpd.read_file(gdf_file_path)

             # Créer une instance de GeographicArea pour chaque forme
            if not selected_rayon : selected_rayon=3
            for index, row in gdf.iterrows():
                if selected_attribute != "aucun":
                    geographic_area = Zone.objects.create(
                    name=row[selected_attribute],
                    geom=GEOSGeometry(dumps(row['geometry'])),
                    active=True,
                    category=selected_category,
                    rayon = selected_rayon
                )
                else :
                    characters = string.ascii_letters + string.digits
                    selected_attribute = "Zone_"+''.join(random.choice(characters) for _ in range(4))
                    geographic_area = Zone.objects.create(
                        name=selected_attribute,
                        #geom=row['geometry'],
                        geom=GEOSGeometry(dumps(row['geometry'])),
                        active = True,
                        category = selected_category,
                        rayon = selected_rayon,
                    )
                    geographic_area.save()

            # print("###########instance creé#############")
            return redirect('forecast:georaphic_area_list')

            ######################
    else:
        form = ShapefileUploadForm()

    return render(request, 'zones/shapefile.html', {'form': form, 'attribut_columns': attribut_columns,'category_choices':category_choices,'rayon':selected_rayon,'shapefile':shapefile})

def save_geographic_area(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        shapefile = request.FILES.get('shapefile')

        #shapefile_path = request.session.get('shapefile_path', None)

        selected_attribute = request.POST.get('selected_attribute')
        selected_category=request.POST.get('selected_category')
        selected_rayon=request.POST.get('rayon')
        # print("###########",shapefile,"##########",selected_attribute,"#########",selected_category)
        #path_without_vsizip = shapefile_path.replace('/vsizip/', '')
        # print("##################path",shapefile)
        gdf = gpd.read_file(shapefile.temporary_file_path())
        print("***********")
        print(gdf)

        # Créer une instance de GeographicArea pour chaque forme
        for index, row in gdf.iterrows():
            geographic_area = Zone.objects.create(
                name=row[selected_attribute],  # Vous pouvez utiliser row[selected_attribute] ou d'autres champs selon vos besoins
                geom=row['geometry'],  # Assurez-vous que le nom de la colonne de géométrie est correct
                active = True,
                category = selected_category,
                rayon = selected_rayon
            )
            geographic_area.save()

        # print("###########instance creé#############")

        """ try:
        #gdf = gpd.read_file(shapefile.temporary_file_path())

        # Lire le shapefile pour obtenir les géométries
            #gdf = gpd.read_file(f'/vsizip/{shapefile_url}')
            print("##################path",shapefile.temporary_file_path())
            gdf = gpd.read_file(shapefile.temporary_file_path())

            # Créer une instance de GeographicArea pour chaque forme
            for index, row in gdf.iterrows():
                geographic_area = Zone.objects.create(
                    name=row[selected_attribute],  # Vous pouvez utiliser row[selected_attribute] ou d'autres champs selon vos besoins
                    geom=row['geometry'],  # Assurez-vous que le nom de la colonne de géométrie est correct
                    active = True,
                    category = selected_category,
                )

            print("###########instance creé#############")
            # Rediriger ou effectuer d'autres actions après l'enregistrement
            return redirect('georaphic_area_list')
        except Exception as e:
            # Gérer les erreurs ici
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', 'shapefile_view'))  # Rediriger vers la page précédente
 """
    # Gérer les autres cas si nécessaire
    return redirect('forecast:georaphic_area_list')

class SaveMergedZoneView(ZonePermission, View):
    template_name = 'zones/save_merged_georaphic_area.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Récupérer les données du formulaire directement depuis la requête
        name = request.POST.get('name')
        category = request.POST.get('category')
        preserver_lines = request.POST.get('preserver_lines')
        # Récupérer les IDs sélectionnés à partir des paramètres de requête
        selected_ids = request.POST.get('selected_ids')
        selected_ids_list = json.loads(selected_ids)
        # print("##############",selected_ids)

        # Convertir les IDs en entiers
        #select_ids = [int(id) for id in selected_ids_list]


        # Récupérer les instances sélectionnées
        selected_instances = Zone.objects.filter(pk__in=selected_ids_list)

        # Fusionner les géométries sélectionnées en une seule géométrie
        if preserver_lines : merged_geometry = self.concat_geometries(selected_instances) 
        else : merged_geometry = self.merge_geometries(selected_instances)
        

        # Créer une nouvelle instance de Zone avec la géométrie fusionnée
        new_georaphic_area = Zone(
            name=name,
            category=category,
            geom=merged_geometry,
            active=True
        )
        new_georaphic_area.save()

        #return HttpResponse('Fusion réussie!')
        return redirect('forecast:georaphic_area_list')  # Rediriger vers la liste après la fusion



    def merge_geometries(self, georaphic_areas):
        # Fusionner les géométries en une seule géométrie
        merged_geometry = None

        for area in georaphic_areas:
            if merged_geometry is None:
                merged_geometry = area.geom
            else:
                merged_geometry = merged_geometry.union(area.geom)
        return merged_geometry
    def concat_geometries(self, georaphic_areas):
        # Fusionner les géométries en une seule géométrie
        merged_geometry = None
        geometries = [area.geom for area in georaphic_areas]
        all_polygons = []
        for geom in geometries:  # où geometries = [g1, g2, ...] et g1 peut être Polygon ou MultiPolygon
            if isinstance(geom, Polygon):
                all_polygons.append(geom)
            elif isinstance(geom, MultiPolygon):
                all_polygons.extend(geom)  # déplie les sous-polygones

        merged_geometry = MultiPolygon(*all_polygons)
        return merged_geometry
