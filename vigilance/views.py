# vigilance/views.py

import geopandas as gpd
import folium
import datetime
import pandas as pd
import json
import pytz
import uuid
import traceback
import os
import xml.etree.ElementTree as ET
import io
import base64
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from .forms import VigilanceForm
from .models import VigimetProvinceAuto
from .models import VigimetProvinceProd
from django.db.models import F, Func, Value, IntegerField, FloatField, TextField
from django.db.models.functions import Cast, JSONObject
from django.views.decorators.csrf import csrf_exempt
from folium.plugins import Draw
from shapely.geometry import shape
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q
from django.core.serializers import serialize
from django.utils import timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from django.utils.text import slugify
from django.db import connection
from django.db.models import Max
from django.conf import settings
from shapely import wkt
from dicttoxml import dicttoxml
from django.contrib.auth.decorators import permission_required

PHENOMENE_CODES = {
    'vc': ('Vague de chaleur', 'HW'),
    'vf': ('Vague de froid', 'CW'),
    'rr': ('Fortes précipitations', 'HR'),
    'wind': ('Vents forts', 'WS'),
    'po': ('Tempête de poussière', 'DU'),
    'ts': ('Orages', 'TS'),
}
def generate_map(param, forecast_date, source):
    # Choix du modèle en fonction de la source
    if source == 'expert':
        Model = VigimetProvinceProd
    elif source == 'gfs':
        Model = VigimetProvinceAuto

    # Première requête : toutes les provinces sauf celle avec province_id = 2371241
    queryset_provinces = Model.objects.filter(param=param, province_id__in=range(1, 55))

    # Deuxième requête : uniquement la province_id = 2371241 (zones personnalisées)
    queryset_zones = Model.objects.filter(param=param).exclude(province_id__in=range(1, 55))

    # Appliquer le filtre sur forecast_date si fourni
    if forecast_date:
        queryset_provinces = queryset_provinces.filter(forecast_date=forecast_date)
        queryset_zones = queryset_zones.filter(forecast_date=forecast_date)

    # Préparation des données
    data = []

    # D’abord les provinces
    for obj in queryset_provinces:
        if obj.geom:
            data.append({
                'province_id': obj.province_id,
                'province_name': obj.province_name,
                'forecast_date': obj.forecast_date,
                'param': obj.param,
                'vigilance_level': int(obj.details.get('level', 0)),
                'value': obj.details.get('value', ''),
                'start_datetime': obj.details.get('start_datetime', ''),
                'end_datetime': obj.details.get('end_datetime', ''),
                'zone': obj.details.get('zone', ''),
                'smin': obj.details.get('smin', '#'),
                'smax': obj.details.get('smax', '#'),
                'comment': obj.details.get('comment', ''),
                'geometry': shape(json.loads(obj.geom.geojson))
            })

    # Puis les zones personnalisées (province_id = 2371241)
    for obj in queryset_zones:
        if obj.geom:
            data.append({
                'province_id': obj.province_id,
                'province_name': obj.province_name,
                'forecast_date': obj.forecast_date,
                'param': obj.param,
                'vigilance_level': int(obj.details.get('level', 0)),
                'value': obj.details.get('value', ''),
                'start_datetime': obj.details.get('start_datetime', ''),
                'end_datetime': obj.details.get('end_datetime', ''),
                'zone': obj.details.get('zone', ''),
                'smin': obj.details.get('smin', '#'),
                'smax': obj.details.get('smax', '#'),
                'comment': obj.details.get('comment', ''),
                'geometry': shape(json.loads(obj.geom.geojson))
            })
    if not data:
        return "<p>Aucune donnée disponible pour les paramètres spécifiés.</p>"

    df = pd.DataFrame(data)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    gdf['forecast_date'] = gdf['forecast_date'].astype(str)

    # Couleurs de vigilance
    colors = {
        0: '#00FF00',
        1: '#FFFF00',
        2: '#FFA500',
        3: '#FF0000',
        None: '#808080'
    }

    def style_function(feature):
        vigilance = feature['properties'].get('vigilance_level')
        province_id = feature['properties'].get('province_id')
        
        fill_opacity = 1 if province_id == 9999 else 1
        
        return {
            'fillColor': colors.get(vigilance, '#808080'),
            'color': 'black',
            'weight': 1,
            'fillOpacity': fill_opacity,
        }

    def popup_html(feature):
        props = feature['properties']
        province_name = props.get('province_name', 'Inconnu')
        province_id = props.get('province_id', '')
        vigilance_level = props.get('vigilance_level')
        forecast_date = props.get('forecast_date', '')
        param = props.get('param', '')
        value = props.get('value', '')
        start_datetime = props.get('start_datetime', '')
        end_datetime = props.get('end_datetime', '')
        smin = props.get('smin', '#')
        smax = props.get('smax', '#')
        zone = props.get('zone', '')
        comment = props.get('comment', '')
        if start_datetime == '':
            start_datetime = datetime.datetime.combine(
                datetime.datetime.strptime(forecast_date, '%Y-%m-%d').date(),
                datetime.time.min
            ).strftime('%Y-%m-%dT%H:%M')

        if end_datetime == '':
            end_datetime = datetime.datetime.combine(
                datetime.datetime.strptime(forecast_date, '%Y-%m-%d').date(),
                datetime.time.max
            ).strftime('%Y-%m-%dT%H:%M')

        color_buttons_html = ""
        for level, color in colors.items():
            if level is not None:
                selected = "selected" if level == vigilance_level else ""
                color_buttons_html += f"""
                <div class="color-btn {selected}" style="background-color: {color};" 
                     data-level="{level}" title="Niveau {level}"></div>"""

        hidden = 'style="display: none;"' if source != 'expert' else ''
        disabled = 'disabled' if source != 'expert' else ''
        html = f"""
        <input type="hidden" value="{forecast_date}" class="forecast_date">
        <input type="hidden" value="{param}" class="param">
        <div class="popup-content" data-province-id="{province_id}">
            <div>
                <label><b>Zone:</b></label>
                <input type="text" class="editable-value" id="zone" value="{zone}" {disabled}/>
            </div>  
            <div>
                <label><b>Valeur:</b></label>
                <input type="text" class="editable-value" id="val" value="{value}" {disabled}/>
            </div>            
            <div>
                <label><b>Date début:</b></label>
                <input type="datetime-local" class="start-datetime editable-value" id="start-datetime" value="{start_datetime}" {disabled}/>
            </div>
            
            <div>
                <label><b>Date fin:</b></label>
                <input type="datetime-local" class="end-datetime editable-value" id="end-datetime" value="{end_datetime}" {disabled}/>
            </div>

            <div style="display: flex; gap: 20px; margin-bottom: 8px;">
                <div><b>Smin :</b> {smin}</div>
                <div><b>Smax :</b> {smax}</div>
            </div>
            <div {hidden}>
            <div class="color-buttons-container" data-province-id="{province_id}">
                {color_buttons_html}
            </div>

            <textarea class="comment-textarea" placeholder="Ajouter un commentaire..."></textarea>
            <button class="save-btn" {disabled}>Enregistrer</button>
            <div class="status-msg"></div>
            </div>
        </div>

        <script>
            (function() {{
                const container = document.currentScript.parentNode.querySelector('.popup-content');
                const colorButtons = container.querySelectorAll('.color-btn');
                let selectedButton = container.querySelector('.color-btn.selected');
                colorButtons.forEach(btn => {{
                    btn.addEventListener('click', () => {{
                        if (selectedButton) selectedButton.classList.remove('selected');
                        btn.classList.add('selected');
                        selectedButton = btn;
                    }});
                }});
            }})();
        </script>
        """

        return html
    # Séparer les polygones normaux et combinés
    gdf_normal = gdf[gdf['province_id'] != 9999]
    gdf_combined = gdf[gdf['province_id'] == 9999]
    gdf = pd.concat([gdf_normal, gdf_combined], ignore_index=True)

    # Ajouter les popups HTML au GeoDataFrame
    gdf['popup_html'] = gdf.apply(lambda row: popup_html({'properties': row}), axis=1)

    # Création de la carte
    center_lat, center_lon = 11.5, -1.2
    zoom_level = 7

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, tiles='cartodbpositron', control_scale=True)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles © Esri — Source: Esri, Garmin, USGS, NGA, EPA, NPS',
        name='Esri World Topo Map',
        overlay=False,
        control=True
    ).add_to(m)

    if source == 'expert':
        draw = Draw(
            export=False,
            position='topleft',
            draw_options={
                'polyline': False,
                'circlemarker': False,
                'marker': False,
                'rectangle': False,
                'circle': False,
                'polygon': {
                    'shapeOptions': {
                        'color': 'gray', 'fill': True, 'fillColor': 'green', 'fillOpacity': 0
                    }
                }
            },
            edit_options={'edit': False}
        )
        draw.add_to(m)

    tooltip = folium.GeoJsonTooltip(
        fields=['zone', 'vigilance_level', 'value', 'smin', 'smax', 'forecast_date'],
        aliases=['Zone', f'Vigilance {param.upper()}', 'Valeur', 'Smin', 'Smax', 'Date'],
        localize=True,
        labels=True,
        sticky=False
    )

    popup = folium.GeoJsonPopup(
        fields=['popup_html'],
        labels=False,
        localize=True,
        parse_html=True,
        max_width=400
    )

    gj = folium.GeoJson(
        gdf,
        style_function=style_function,
        tooltip=tooltip,
        popup=popup,
        name=f"Vigilance {param.upper()}"
    )
    gj.add_to(m)

    bounds = gdf.total_bounds

    # Ajout des ressources CSS et JS
    m.get_root().header.add_child(folium.Element('<link rel="stylesheet" href="/static/css/popup.css">'))
    m.get_root().header.add_child(folium.Element('<script src="https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js"></script>'))
    m.get_root().header.add_child(folium.Element('<script src="/static/js/popup_behavior.js"></script>'))
    m.get_root().html.add_child(folium.Element(f'''
        <script>
            window.vigilanceContext = {{
                param: "{param}",
                forecast_date: "{forecast_date}"
            }};
        </script>
    '''))
    map_html = m._repr_html_()
    map_html = map_html.replace("Make this Notebook Trusted to load map: File -> Trust Notebook", "En cours de chargement ...")
    return map_html

@permission_required('vigilance.view_vigilance', raise_exception=True)
def vigilance_map(request):
    initial_data = {'date': datetime.date.today().strftime('%Y-%m-%d')}
    form = VigilanceForm(request.GET or None, initial=initial_data)
    param = 'vc'
    source = 'expert'
    date_str = initial_data['date']
    map_html = None

    if form.is_valid():
        param = form.cleaned_data['param']
        date_obj = form.cleaned_data['date']
        source = form.cleaned_data['source']
        date_str = date_obj.strftime('%Y-%m-%d')
        map_html = generate_map(param, date_str, source)
    else:
        map_html = generate_map(param, date_str, source)

    context = {
        'form': form,
        'param': param,
        'source': source,
        'date': date_str or "Dernière date disponible",
        'map': map_html,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('vigilance/map_fragment.html', {'map': map_html})
        return JsonResponse({'map_html': html})

    return render(request, 'vigilance/map.html', context)

@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt
def edit_vigilance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            province_id = data.get('province_id')
            level = data.get('vigilance')
            comment = data.get('comment', '')
            param = data.get('param', '')
            forecast_date = data.get('forecast_date', '')
            val = data.get('val', '')
            start_datetime = data.get('start_datetime', '')
            end_datetime = data.get('end_datetime', '')
            zone = data.get('zone', '')

            # Convertir forecast_date en objet date si besoin
            if isinstance(forecast_date, str):
                forecast_date = datetime.datetime.strptime(forecast_date, "%Y-%m-%d").date()

            obj = VigimetProvinceProd.objects.filter(
                province_id=province_id,
                forecast_date=forecast_date,
                param=param
            ).first()

            if obj:
                # Mise à jour des champs JSON
                details = obj.details or {}

                if level is not None:
                    details['level'] = int(level)
                if comment != '':
                    details['comment'] = comment
                if val != '':
                    try:
                        details['value'] = float(val)
                    except ValueError:
                        pass  # ignorer si val n'est pas convertible
                if start_datetime != '':
                    details['start_datetime'] = start_datetime
                if end_datetime != '':
                    details['end_datetime'] = end_datetime
                if zone != '':
                    details['zone'] = zone

                obj.details = details
                obj.save()

                VigimetProvinceProd.objects.filter(
                    forecast_date=forecast_date,
                    param=param
                ).update(status=1)


                return JsonResponse({"success": "Object updated", "details": obj.details})
            else:
                return JsonResponse({"error": "Object not found"}, status=404)

        except Exception as e:
            import traceback
            traceback.print_exc()  

            return JsonResponse({"error": str(e)}, status=500)

@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt  # À retirer si CSRF est géré côté front
def add_vigilance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forecastDate = data.get('forecastDate', '')
            param = data.get('param', '')
            level = data.get('level', '')
            zone = data.get('zone', '')
            value = data.get('value', '')
            startdatetime = data.get('startdatetime', '')
            enddatetime = data.get('enddatetime', '')
            comment = data.get('comment', '')
            geom_geojson = data.get('geom')
            
            last_id = VigimetProvinceProd.objects.aggregate(Max('id'))['id__max']
            new_id = last_id + 1 if last_id is not None else uuid.uuid4().int >> 64  # UUID réduit à 64 bits
            count = VigimetProvinceProd.objects.filter(
                forecast_date=forecastDate,
                param=param,
                province_id__gt=54
            ).count()

            if not geom_geojson:
                print("Erreur : pas de géométrie reçue")
                return JsonResponse({'success': False, 'error': 'No geometry provided.'})

            # Création de la géométrie et définition du SRID
            geom = GEOSGeometry(json.dumps(geom_geojson))
            geom.srid = 4326

            # Appel à la fonction PostGIS pour récupérer l'intersection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT mask.intersect_with_country(ST_SetSRID(ST_GeomFromText(%s), %s))
                """, [geom.wkt, geom.srid])
                result = cursor.fetchone()

            if result is None or result[0] is None:
                print("Intersection vide ou nulle, insertion annulée.")
                return JsonResponse({'success': False, 'error': 'No intersection with country.'})

            intersection_wkb = result[0]
            intersection_geom = GEOSGeometry(intersection_wkb, srid=4326)

            # Insertion dans la base avec la géométrie intersectionnée
            new_entry = VigimetProvinceProd.objects.create(
                province_id=new_id,
                province_name = f"Zone personnalisée {count + 1}",
                forecast_date=forecastDate,
                param=param,
                details={
                    'level': level,
                    'value': value,
                    'zone': zone,
                    'startdatetime': startdatetime,
                    'enddatetime': enddatetime,
                    'comment': comment
                },
                geom=intersection_geom,
            )

            print(f"Insertion en base réussie : ID {new_entry.id}")

            

            return JsonResponse({'success': True})

        except Exception as e:
            print("Exception:", str(e))
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        print("Mauvaise méthode HTTP :", request.method)
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'})

@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt  # À enlever si tu gères CSRF côté frontend
def get_vigilance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forecast_date = data.get('forecastDate', '')
            param = data.get('param', '')
            print("=== Requête AJAX reçue pour récupération GeoJSON ===")
            print("Date:", forecast_date)
            print("Paramètre:", param)

            # Queryset de base
            base_queryset = VigimetProvinceProd.objects.all()

            if forecast_date:
                base_queryset = base_queryset.filter(forecast_date=forecast_date)

            if param:
                base_queryset = base_queryset.filter(param=param)

            # 1. D'abord les features avec province_id ≠ 9999
            normal_zones_qs = base_queryset.exclude(province_id=9999)
            geojson_normal = json.loads(serialize(
                'geojson',
                normal_zones_qs,
                geometry_field='geom',
                fields=('province_id', 'province_name', 'details')
            ))

            # 2. Ensuite les features avec province_id == 9999
            custom_zones_qs = base_queryset.filter(province_id=9999)
            geojson_custom = json.loads(serialize(
                'geojson',
                custom_zones_qs,
                geometry_field='geom',
                fields=('province_id', 'province_name', 'details')
            ))

            # Combiner les deux listes de features
            combined_geojson = {
                "type": "FeatureCollection",
                "features": geojson_normal['features'] + geojson_custom['features']
            }

            print(f"Total features retournées : {len(combined_geojson['features'])}")
            return JsonResponse(combined_geojson, safe=False)

        except Exception as e:
            print("Erreur lors de la récupération GeoJSON:", str(e))
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    else:
        print("Mauvaise méthode HTTP :", request.method)
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'}, status=405)

@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt  # À enlever si tu gères CSRF côté front correctement
def clear_vigilance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forecastDate = data.get('forecastDate', '')
            param = data.get('param', '')
            print(param)

            # Suppression complète des entrées dans VigimetProvinceProd (filtrées sur forecast_date et param)
            VigimetProvinceProd.objects.filter(forecast_date=forecastDate, param=param).delete()
            print(f"VigimetProvinceProd nettoyée pour forecast_date={forecastDate} et param={param}")

            # Récupération des données dans VigimetProvinceAuto (sans province_id=9999)
            auto_entries = VigimetProvinceAuto.objects.filter(
                forecast_date=forecastDate,
                param=param
            ).exclude(province_id=9999)

            # Insertion dans VigimetProvinceProd avec level forcé à 0
            prod_entries_to_create = []
            for auto_entry in auto_entries:
                details = auto_entry.details or {}
                details['level'] = 0
                details['value'] = ''

                prod_entry = VigimetProvinceProd(
                   
                    province_id=auto_entry.province_id,
                    province_name=auto_entry.province_name,
                    forecast_date=auto_entry.forecast_date,
                    param=auto_entry.param,
                    details=auto_entry.details,
                    geom=auto_entry.geom,
                )
                prod_entries_to_create.append(prod_entry)

            VigimetProvinceProd.objects.bulk_create(prod_entries_to_create)

            print(f"Nombre de lignes insérées depuis VigimetProvinceAuto : {len(prod_entries_to_create)}")

            return JsonResponse({'success': True})

        except Exception as e:
            print("Exception:", str(e))
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        print("Mauvaise méthode HTTP :", request.method)
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'})
@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt  # À enlever si tu gères CSRF côté front correctement
def revoke_vigilance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forecastDate = data.get('forecastDate', '')
            param = data.get('param', '')
            print(f"Param: {param}, ForecastDate: {forecastDate}")

            # Suppression des anciennes entrées dans VigimetProvinceProd pour éviter doublons
            VigimetProvinceProd.objects.filter(forecast_date=forecastDate, param=param).delete()
            print(f"VigimetProvinceProd nettoyée pour forecast_date={forecastDate} et param={param}")

            # Récupération des données dans VigimetProvinceAuto (sans modification du level)
            auto_entries = VigimetProvinceAuto.objects.filter(
                forecast_date=forecastDate,
                param=param
            )

            prod_entries_to_create = []
            for auto_entry in auto_entries:
                prod_entry = VigimetProvinceProd(
                    province_id=auto_entry.province_id,
                    province_name=auto_entry.province_name,
                    forecast_date=auto_entry.forecast_date,
                    param=auto_entry.param,
                    details=auto_entry.details,  
                    geom=auto_entry.geom,
                )
                prod_entries_to_create.append(prod_entry)

            # Insertion bulk
            VigimetProvinceProd.objects.bulk_create(prod_entries_to_create)

            print(f"Nombre de lignes insérées depuis VigimetProvinceAuto : {len(prod_entries_to_create)}")

            return JsonResponse({'success': True})

        except Exception as e:
            print("Exception:", str(e))
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        print("Mauvaise méthode HTTP :", request.method)
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'})



def geom_to_polygon_string(geom):
    """
    Convertit un objet GEOSGeometry Django (MultiPolygon ou Polygon) en chaîne CAP <polygon>.
    Format CAP attendu : lat,lon lat,lon ...
    """
    try:
        if geom.geom_type == 'Polygon':
            exterior_ring = geom.coords[0]
        elif geom.geom_type == 'MultiPolygon':
            exterior_ring = geom[0].coords[0]
        else:
            return ""

        points = ["{:.4f},{:.4f}".format(lat, lon) for lon, lat in exterior_ring]
        return " ".join(points)
    except Exception as e:
        print("Erreur géométrie:", e)
        return ""


def get_cap_severity(level):
    try:
        level = int(level)
    except:
        return "Unknown"

    if level == 0:
        return "Minor"
    elif level == 1:
        return "Moderate"
    elif level == 2:
        return "Severe"
    elif level == 3:
        return "Extreme"
    else:
        return "Unknown"


@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt
def generate_cap(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:

        ALERT_TEXTS = {
            'vc': {  # Vague de chaleur (Heatwave)
                'headline': "Alerte chaleur {zone} - Niveau {level_label}",
                'description': "Niveau de vigilance chaleur : {level_label}. Températures exceptionnellement élevées attendues.",
                'instruction': "Buvez régulièrement de l’eau, évitez les efforts physiques aux heures les plus chaudes, restez à l’ombre et surveillez les personnes vulnérables."
            },
            'vf': {  # Vague de froid (Cold wave)
                'headline': "Alerte froid {zone} - Niveau {level_label}",
                'description': "Risques liés à un froid intense et prolongé.",
                'instruction': "Couvrez-vous chaudement, limitez les sorties non essentielles, protégez les personnes vulnérables et évitez les canalisations gelées."
            },
            'rr': {  # Fortes précipitations (Heavy rain)
                'headline': "Alerte pluies intenses {zone} - Niveau {level_label}",
                'description': "Précipitations intenses susceptibles de provoquer des inondations.",
                'instruction': "Évitez les zones inondables, ne traversez pas les cours d’eau en crue et suivez les consignes des autorités locales."
            },
            'wind': {  # Vents forts (Strong winds)
                'headline': "Alerte vents forts {zone} - Niveau {level_label}",
                'description': "Risques liés à des rafales de vent pouvant causer des dégâts matériels.",
                'instruction': "Fixez ou rentrez les objets susceptibles d’être emportés, évitez les déplacements en zones exposées et ne vous abritez pas sous les arbres."
            },
            'po': {  # Tempête de poussière (Dust storm)
                'headline': "Alerte tempête de poussière {zone} - Niveau {level_label}",
                'description': "Visibilité fortement réduite due à une tempête de poussière.",
                'instruction': "Portez un masque ou protégez voies respiratoires, limitez les sorties, fermez portes et fenêtres et conduisez avec prudence."
            },
            'ts': {  # Orages (Thunderstorms)
                'headline': "Alerte orages {zone} - Niveau {level_label}",
                'description': "Orages violents attendus avec risques de foudre, fortes pluies, rafales et grêle.",
                'instruction': "Évitez les zones découvertes, débranchez les appareils électriques, ne vous abritez pas sous les arbres et soyez vigilant lors des déplacements."
            }
        }

        data = json.loads(request.body)
        forecast_date = data.get('forecastDate')
        param = data.get('param')

        queryset = VigimetProvinceProd.objects.all()

        if forecast_date:
            queryset = queryset.filter(forecast_date=forecast_date)
        if param:
            queryset = queryset.filter(param=param)

        now = timezone.now()
        cap_messages = []

        for item in queryset:
            id = item.id
            province = item.province_name
            param = item.param
            details = item.details or {}
            zone = details.get('zone')
            start_datetime = details.get('start_datetime')
            end_datetime = details.get('end_datetime')
            geom = item.geom
            print(details.get('level', '0'))
            try:
                level_int = int(details.get('level', '0'))
            except (ValueError, TypeError):
                level_int = 0

            if level_int < 2:
                continue

            if not geom:
                continue
            LEVEL_LABELS = {
                0: "Vert",
                1: "Jaune",
                2: "Orange",
                3: "Rouge",
            }

            SEVERITY_LABELS = {
                0: "Minor",
                1: "Moderate",
                2: "Severe",
                3: "Extreme",
            }
            level_label = LEVEL_LABELS.get(level_int, "Indéfini")
            severity_label = SEVERITY_LABELS.get(level_int, "Indéfini")

            smax = details.get('smax', '')
            smin = details.get('smin', '')
            value = details.get('value', '')

            alert = Element("alert", xmlns="urn:oasis:names:tc:emergency:cap:1.2")

            SubElement(alert, "identifier").text = f"{param}-{forecast_date.replace('-', '')}-{slugify(zone)}"
            SubElement(alert, "sender").text = "meteoburkina.bf"
            SubElement(alert, "sent").text = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")

            # status, msgType, scope avec valeurs par défaut si vide
            SubElement(alert, "status").text = details.get('status', 'Actual')
            SubElement(alert, "msgType").text = details.get('msgType','Alert')
            SubElement(alert, "scope").text = details.get('scope', 'Public')

            info = SubElement(alert, "info")
            SubElement(info, "language").text = "fr-FR"
            SubElement(info, "category").text = "Met"
            event_label, event_code = PHENOMENE_CODES.get(param, ('Phénomène météorologique dangereux', 'XX'))
            SubElement(info, "event").text = details.get('event', 'Phénomène météorologique dangereux')
            SubElement(info, "responseType").text = details.get('responseType', 'Avoid')
            
            SubElement(info, "urgency").text = details.get('urgency', 'Immediate')
            SubElement(info, "severity").text = severity_label
            SubElement(info, "certainty").text = details.get('certainty', 'Possible')

            # Gestion format date start_datetime et end_datetime
            if start_datetime is None or end_datetime is None:
                forecast_date_obj = datetime.datetime.strptime(forecast_date, "%Y-%m-%d").date()
                start_dt_obj = datetime.datetime.combine(forecast_date_obj, datetime.time(0, 0))
                end_dt_obj = datetime.datetime.combine(forecast_date_obj, datetime.time(23, 59))
            else:
                # Essayer de parser avec secondes, sinon sans secondes
                try:
                    start_dt_obj = datetime.datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    start_dt_obj = datetime.datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M")
                try:
                    end_dt_obj = datetime.datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    end_dt_obj = datetime.datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M")

            SubElement(info, "effective").text = start_dt_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            SubElement(info, "expires").text = end_dt_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")

            SubElement(info, "senderName").text = "Agence Nationale de la Météorologie du Burkina Faso (ANAM-BF)"

            texts = ALERT_TEXTS.get(param, {
                'headline': "Alerte météo {zone} - Niveau {level_int}",
                'description': "Phénomène météorologique dangereux détecté.",
                'instruction': "Suivez les recommandations officielles."
            })

            SubElement(info, "headline").text = texts['headline'].format(zone=zone, level_label=level_label)
            SubElement(info, "description").text = details.get('comment', texts['description'].format(zone=zone, level_label=level_label))
            SubElement(info, "instruction").text = details.get('instruction', texts['instruction'])
            SubElement(info, "web").text = "https://www.meteoburkina.bf/"

            area = SubElement(info, "area")
            SubElement(area, "areaDesc").text = zone
            polygon_str = geom_to_polygon_string(geom)
            if polygon_str:
                SubElement(area, "polygon").text = polygon_str

            xml_string = tostring(alert, encoding='unicode')
            cap_messages.append({
                'id': id,
                'zone': zone,
                'cap': xml_string
            })

        return cap_messages

    except Exception as e:
        print("Erreur lors de la génération des messages CAP :", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@permission_required('vigilance.edit_vigilance', raise_exception=True)
def generate_cap_messages(request):
    cap_messages = generate_cap(request)
    return JsonResponse({"messages": cap_messages})


def format_datetime_short(dt_str, start=True):
    try:
        dt = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        date_only = dt.date().isoformat()
        return f"{date_only}T00:00" if start else f"{date_only}T23:59"
    except Exception:
        return dt_str  # Si parsing échoue, renvoyer brut

# Fonction utilitaire pour formater la date ISO complète en "YYYY-MM-DDTHH:MM"
def format_datetime_compatibility(dt_str, start=True):
    if not dt_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%dT%H:%M")
    except Exception:
        return dt_str  # Retourne brut si erreur

@permission_required('vigilance.edit_vigilance', raise_exception=True)
@csrf_exempt
def save_cap(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        idZone = data.get('idZone')
        cap_xml = data.get('capXml')

        if not cap_xml:
            return JsonResponse({'success': False, 'error': 'CAP XML manquant'}, status=400)

        # 1. Analyse du XML
        try:
            root = ET.fromstring(cap_xml)
            ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

            identifier_elem = root.find('cap:identifier', ns)
            if identifier_elem is None or not identifier_elem.text:
                raise ValueError("Balise <identifier> introuvable ou vide")

            filename = f"{identifier_elem.text}.xml"
        except Exception:
            return JsonResponse({'success': False, 'error': 'XML invalide ou <identifier> manquant'}, status=400)

        # 3. Extraction des données à enregistrer dans `details`
        new_values = {}

        # a) Champs de niveau <alert>
        for tag in ['identifier', 'sender', 'sent', 'status', 'msgType', 'scope']:
            elem = root.find(f'cap:{tag}', ns)
            if elem is not None and elem.text:
                value = elem.text.strip()
                if tag == 'sent':
                    value = format_datetime_compatibility(value)
                new_values[tag] = value

        # b) Champs de niveau <info>
        info = root.find('cap:info', ns)
        if info is not None:
            for child in info:
                if child.tag.endswith('area'):
                    continue
                tag = child.tag.split('}')[-1]
                text = (child.text or '').strip()

                if tag == 'effective':
                    new_values['start_datetime'] = format_datetime_compatibility(text, start=True)
                elif tag == 'expires':
                    new_values['end_datetime'] = format_datetime_compatibility(text, start=False)
                elif tag == 'description':
                    new_values['comment'] = text
                else:
                    new_values[tag] = text

        # 4. Sauvegarde dans la base de données
        try:
            zone = VigimetProvinceProd.objects.get(id=idZone)
            existing_detail = zone.details or {}

            for key, value in new_values.items():
                existing_detail[key] = value

            zone.details = existing_detail
            zone.save()

        except VigimetProvinceProd.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Zone introuvable'}, status=404)

        return JsonResponse({
            'success': True
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@permission_required('vigilance.view_vigilance', raise_exception=True)
@csrf_exempt
def get_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forecastDate = data.get('forecastDate', '')
            param = data.get('param', '')
            print(f"Param: {param}, ForecastDate: {forecastDate}")

            queryset_provinces = VigimetProvinceProd.objects.filter(param=param).exclude(province_id__in=range(1, 55))
            queryset_provinces = queryset_provinces.filter(forecast_date=forecastDate)

            queryset_zones = VigimetProvinceProd.objects.filter(param=param, province_id__in=range(1, 55))
            queryset_zones = queryset_zones.filter(forecast_date=forecastDate)
            queryset = queryset_provinces.union(queryset_zones)

            if not queryset.exists():
                return JsonResponse({'success': False, 'error': 'Aucun enregistrement trouvé.'})

            # Récupération et formatage de la date depuis la base
            date_obj = None
            try:
                date_obj = queryset.first().forecast_date
            except Exception as e:
                print("Erreur récupération date depuis queryset :", e)
                date_obj = None

            jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

            if date_obj:
                jour_semaine = jours[date_obj.weekday()]
                date_formatted = f"{jour_semaine} {date_obj.day} {mois[date_obj.month - 1]} {date_obj.year}"
            else:
                # Fallback sur la chaîne reçue
                try:
                    date_obj_from_str = datetime.strptime(forecastDate, '%Y-%m-%d')
                    jour_semaine = jours[date_obj_from_str.weekday()]
                    date_formatted = f"{jour_semaine} {date_obj_from_str.day} {mois[date_obj_from_str.month - 1]} {date_obj_from_str.year}"
                except Exception as e:
                    print("Erreur format date fallback :", e)
                    date_formatted = forecastDate

            level_colors = {
                0: '#00FF00',  # vert
                1: '#FFFF00',  # jaune
                2: '#FFA500',  # orange
                3: '#FF0000',  # rouge
            }

            geoms = []
            colors = []

            for record in queryset:
                details = {}
                if record.details:
                    try:
                        if isinstance(record.details, str):
                            details = json.loads(record.details)
                        elif isinstance(record.details, dict):
                            details = record.details
                    except Exception as e:
                        print(f"Erreur JSON details: {e}")
                        details = {}

                level_int = int(details.get('level', 0))
                color = level_colors.get(level_int, '#808080')  # gris par défaut

                if hasattr(record.geom, 'wkt'):
                    geom_wkt = record.geom.wkt
                else:
                    geom_wkt = record.geom

                geoms.append(wkt.loads(geom_wkt))
                colors.append(color)

            gdf = gpd.GeoDataFrame(geometry=geoms)

            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_facecolor('#ffffff')  # fond blanc

            gdf.plot(ax=ax, color=colors, edgecolor='black')

            titre = PHENOMENE_CODES.get(param, ('Phénomène inconnu', ''))[0]
            ax.text(0.5, 1.07, f"Carte de vigilance - {titre}",
                    transform=ax.transAxes, fontsize=12, ha='center', fontweight='bold')
            # ➕ Ajout de la date de validité
            ax.text(0.5, 1.03, f"Valide : {date_formatted}",
                    transform=ax.transAxes, fontsize=11, ha='center', style='italic', color='dimgray')
            ax.axis('off')

            # Logo en haut à gauche
            try:
                logo_path = os.path.join(settings.BASE_DIR, 'static/images/logo_ANAM.png')
                print("Chemin logo :", logo_path)

                if os.path.isfile(logo_path):
                    logo = mpimg.imread(logo_path)
                    logo_ax = fig.add_axes([0.02, 0.82, 0.15, 0.15], zorder=10)
                    logo_ax.imshow(logo)
                    logo_ax.axis('off')
                else:
                    print("⚠️ Logo introuvable :", logo_path)
            except Exception as e:
                print("⚠️ Erreur logo :", e)

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

            return img_base64

        except Exception as e:
            print("Exception:", str(e))
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        print("Mauvaise méthode HTTP :", request.method)
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'})

@permission_required('vigilance.view_vigilance', raise_exception=True)
def show_image(request):
    img_base64 = get_image(request)
    return JsonResponse({'success': True, 'image_base64': img_base64})

@permission_required('vigilance.view_vigilance', raise_exception=True)
@csrf_exempt
def export(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forecastDate = data.get('forecastDate', '')  # ex: '2025-06-15'
            param = data.get('param', '')

            folder_name = forecastDate.replace('-', '') if forecastDate else 'unknown_date'

            # === Génération des XMLs ===
            cap_messages = generate_cap(request)
            xml_output_dir = os.path.join(settings.MEDIA_ROOT, 'vigilance/cap_xmls', folder_name)
            os.makedirs(xml_output_dir, exist_ok=True)

            file_names = []  # Pour collecter les noms des fichiers générés

            for i, msg in enumerate(cap_messages):
                xml_content = msg.get('cap', '')
                if not isinstance(xml_content, str):
                    xml_content = str(xml_content)

                try:
                    root = ET.fromstring(xml_content)
                    ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
                    identifier = root.find('cap:identifier', ns)
                    identifier_text = identifier.text if identifier is not None else f"unknown_{i+1}"
                except Exception:
                    identifier_text = f"invalid_{i+1}"

                filename = f'{identifier_text}.xml'
                file_path = os.path.join(xml_output_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)

                file_names.append(filename)

            # === Génération de l’image ===
            img_base64 = get_image(request)  # base64 string
            image_path = None
            if img_base64:
                image_output_dir = os.path.join(settings.MEDIA_ROOT, 'vigilance/images', folder_name)
                os.makedirs(image_output_dir, exist_ok=True)

                image_path = os.path.join(image_output_dir, f'{param}-{folder_name}-map.png')
                with open(image_path, 'wb') as img_file:
                    img_file.write(base64.b64decode(img_base64))
            file_names.append(f'{param}-{folder_name}-map.png')

            # === Réponse JSON enrichie ===
            return JsonResponse({
                'success': True,
                'files_created': len(file_names),
                'file_list': file_names,
                'xml_directory': os.path.relpath(xml_output_dir, settings.MEDIA_ROOT),
                'image_path': os.path.relpath(image_path, settings.MEDIA_ROOT) if image_path else None,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'})

