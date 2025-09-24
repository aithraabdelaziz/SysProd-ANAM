# chartmet/utils.py
import os
from datetime import datetime, timedelta
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from django.conf import settings
import locale

from .models import MapObsConfiguration,MapFcstConfiguration, MapModelConfiguration, MapSpatialConfiguration
from observation.models import Observation, Station, ClimatDecades, ClimatMois
from forecast.models import Forecast, Zone
from django.contrib.gis.geos import Point

from django.contrib.gis.geos import GEOSGeometry
from shapely.wkt import dumps as shapely_to_wkt

from bs4 import BeautifulSoup
import yaml
import psycopg2
from psycopg2.extras import RealDictCursor
import math
import pandas as pd
import numpy as np
from pprint import pprint
CONFIG_PATH = 'config.yaml'

from bulletins.models import Echeance
from collections import defaultdict
from functools import lru_cache

import matplotlib.image as mpimg
import matplotlib.patches as patches
from django.db.models import Q

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
def strip_html(text):
    if text : return BeautifulSoup(text, "html.parser").get_text()
    else : return ""
def is_far_enough(x, y, existing, min_dist=0.1):
    for ex, ey in existing:
        if abs(x - ex) < min_dist and abs(y - ey) < min_dist:
            return False
    return True

def organize_obs(data_obs):
    obss={}
    for d in data_obs:
        if d.station not in obss : obss[d.station]={}
        obss[d.station][d.parametre.shortName]=d.observation 
    return obss

def organize_fcst(data_fcst):
    fcts={}
    for d in data_fcst:
        if d.zone not in fcts : fcts[d.zone]={}
        fcts[d.zone][d.parametre.shortName]=d.prevision 
    return fcts
import joblib
import hashlib

def cache_union_geometry(shapefile_path):
    hash_key = hashlib.md5(shapefile_path.encode()).hexdigest()
    cache_path = f"/tmp/unary_union_{hash_key}.joblib"
    if os.path.exists(cache_path):
        return joblib.load(cache_path)
    else:
        shape = gpd.read_file(shapefile_path)
        union = shape.unary_union
        joblib.dump(union, cache_path)
        return union
def cache_geometry(shapefile_path):
    hash_key = hashlib.md5(shapefile_path.encode()).hexdigest()
    cache_path = f"/tmp/shape_borders_{hash_key}.joblib"
    if os.path.exists(cache_path):
        return joblib.load(cache_path)
    else:
        shape = gpd.read_file(shapefile_path)
        return shape

def generate_observation_map(date_string, heure, pk=None):

    import cartopy.crs as ccrs
    date_obs = datetime.strptime(date_string, "%Y-%m-%d")

    try:
        heure = int(heure)
        date_title = (date_obs + timedelta(hours=heure)).strftime("%A %d %B %Y %Hh00").capitalize()
    except Exception:
        name = Echeance.objects.filter(echeance=heure).values_list('name', flat=True).first() or ''
        date_title = f"{date_obs.strftime('%A %d %B %Y')} ({name})"

    if pk:
        configMap = MapObsConfiguration.objects.select_related().get(id=pk)
        identifier = pk
    else:
        configMap = MapObsConfiguration.objects.filter(active=True).first()
        if not configMap:
            configMap, _ = MapObsConfiguration.objects.update_or_create(active=True)
            configMap.save()
            configMap.stations.set(Station.objects.filter(active=True))
        identifier = configMap.id or 0

    stations = list(configMap.stations.all())
    # pprint(f'date={date_obs}, heure={heure}, station__in={stations}')
    data_obs = Observation.objects.filter(date=date_obs, heure=heure, station__in=stations).select_related('station', 'parametre')
    # pprint(data_obs)
    output_base = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'obs_map', date_obs.strftime("%Y/%m/%d"))
    output_path_png = os.path.join(output_base, 'png')
    output_path_html = os.path.join(output_base, 'html')

    os.makedirs(output_path_png, exist_ok=True)
    os.makedirs(output_path_html, exist_ok=True)

    png_file = f'{identifier}_obs_map_{date_obs.strftime("%d%m%Y")}_{heure}.png'
    html_file = f'{identifier}_obs_map_{date_obs.strftime("%d%m%Y")}_{heure}.html'

    full_png_path = os.path.join(output_path_png, png_file)
    full_html_path = os.path.join(output_path_html, html_file)
    public_png_path = os.path.join('/media', 'chartmet', 'obs_map', date_obs.strftime("%Y/%m/%d"), 'png', png_file)
    public_html_path = os.path.join('/media', 'chartmet', 'obs_map', date_obs.strftime("%Y/%m/%d"), 'png', html_file)
    
    
    bfa_shape = cache_geometry(configMap.zip_file.file.path)
    union_geom = cache_union_geometry(configMap.zip_file.file.path)
   
    facecolor = configMap.facecolor
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=facecolor)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    bfa_shape.plot(ax=ax, color=configMap.color_shape, edgecolor=configMap.intern_edgecolor, linewidth=configMap.intern_linewidth)
    gpd.GeoSeries(union_geom).boundary.plot(ax=ax, edgecolor=configMap.border_edgecolor, linewidth=configMap.border_linewidth)   

    ob = organize_obs(data_obs)
    m = folium.Map(location=[12.2383, -1.5616], zoom_start=7, min_zoom=7)
    marker_cluster = MarkerCluster().add_to(m)
    displayed_coords = []
    merged_geom_django = GEOSGeometry(shapely_to_wkt(union_geom))
    
    
    @lru_cache(maxsize=None)
    def load_icon(symb):
        symbole_name = f'{symb}.png'
        real_path = os.path.join(settings.MEDIA_ROOT, 'weathericons', symbole_name)
        return real_path, Image.open(real_path)

    for city, data in ob.items():
        if not isinstance(city.geom, Point) or not city.geom.within(merged_geom_django):
            continue

        x, y = city.geom.x, city.geom.y
        tmin = strip_html(data.get('air_temperature_min', 'NP')) or 'NP'
        tmax = strip_html(data.get('air_temperature_max', 'NP')) or 'NP'
        rr = strip_html(data.get('precipitation_amount', '')) or ''
        symb = strip_html(data.get('symbol_code', 'np')) or 'np'
        if tmin=='NP' and tmax=='NP' and symb=='np' :
            continue

        icon_path, img = load_icon(symb)
        icon = folium.CustomIcon(icon_path, icon_size=(60, 60), icon_anchor=(20, 20))
        iframe = folium.IFrame(f"{city.name} :<br> {symb}<br>T :<span style='color:blue'>{tmin}</span>/<span style='color:red'>{tmax}</span>°C<br>Pluie : {rr}mm")
        popup = folium.Popup(iframe, min_width=150, max_width=200)

        folium.Marker(location=[y, x], icon=icon, popup=popup, tooltip=city.name).add_to(marker_cluster)

        if not is_far_enough(x, y, displayed_coords, min_dist=configMap.min_dist / 100):
            continue

        ab = AnnotationBbox(OffsetImage(img, zoom=0.4), (x, y), frameon=False, pad=0)

        if configMap.temps_sensible : 
            ax.add_artist(ab)
        else : 
            plt.plot(x, y, marker='+', color='black', markersize=2)
            x -=0.15
        
        plt.text(x + 0.2, y, f"{city.name}\n", fontsize=7, bbox=dict(facecolor='white', alpha=0.2, edgecolor='none'))
         
        if configMap.tmin and configMap.tmax :
            plt.text(x + 0.2, y - 0.05, f"{tmin}", color='blue', fontweight='bold', fontsize=7) 
            plt.text(x + 0.2 + len(str(tmin)) * 0.1, y - 0.05, "/", fontsize=6)
            plt.text(x + 0.2 + len(str(tmin)) * 0.1 + 0.1, y - 0.05, f"{tmax}", color='red', fontweight='bold', fontsize=7)
        elif configMap.tmin :
            plt.text(x + 0.2, y - 0.05, f"{tmin}", color='blue', fontweight='bold', fontsize=7)
        elif configMap.tmax :
            plt.text(x + 0.2, y - 0.05, f"{tmax}", color='red', fontweight='bold', fontsize=7)
        if (configMap.tmin or configMap.tmax) and configMap.pluie : plt.text(x + 0.2, y - 0.15, f"{rr}", color='black', fontweight='bold', fontsize=5)
        elif configMap.pluie : plt.text(x + 0.2, y - 0.05, f"{rr}", color='black', fontweight='bold', fontsize=5)

        displayed_coords.append((x, y))

    if configMap.logo :
        img_path = configMap.logo.file 
        logo = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = 0.05 * fig_height_in_pixels  # 5% de la hauteur
        logo_zoom = desired_logo_height / logo.shape[0]  # logo.shape[0] = hauteur en pixels de l'image
        imagebox = OffsetImage(logo, zoom=logo_zoom)
        ab = AnnotationBbox(imagebox, xy=(0.01, 0.01), xycoords='axes fraction',
                            frameon=False, box_alignment=(0, 0))  # coin haut gauche
        ax.add_artist(ab)

    if configMap.legende_1:
        img_path = configMap.legende_1.file 
        legende_1 = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = configMap.taille_legende_1/100 * fig_height_in_pixels  # % de la hauteur
        logo_zoom = desired_logo_height / legende_1.shape[0]  # Hauteur de l'image
        imagebox = OffsetImage(legende_1, zoom=logo_zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(0, 1),              
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(0, 1)          
        )
        ax.add_artist(ab)

    if configMap.legende_2:
        img_path = configMap.legende_2.file 
        legende_2 = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = configMap.taille_legende_2/100 * fig_height_in_pixels  # % de la hauteur
        logo_zoom = desired_logo_height / legende_2.shape[0]  # Hauteur de l'image
        imagebox = OffsetImage(legende_2, zoom=logo_zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(1, 0),              
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(1, 0)          # Alignement du coin bas droit de l'image
        )
        ax.add_artist(ab)

    if configMap.legende_3:
        img_path = configMap.legende_3.file 
        legende_3 = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = configMap.taille_legende_3/100 * fig_height_in_pixels  # % de la hauteur
        logo_zoom = desired_logo_height / legende_3.shape[0]  # Hauteur de l'image
        imagebox = OffsetImage(legende_3, zoom=logo_zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(1, 1),              
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(1, 1)          # Alignement du coin haut droit de l'image
        )
        ax.add_artist(ab)

    # ax.set_xlim([-6, 3])
    # ax.set_ylim([9, 15])
    ax.axis('off')
    # Ajouter un cadre autour de toute la figure
    # fig.patches.extend([
    #     patches.Rectangle(
    #         (0, 0),         # coin inférieur gauche en coordonnées normalisées
    #         1,              # largeur = 100% de la figure
    #         1,              # hauteur = 100% de la figure
    #         linewidth=2,
    #         edgecolor='gray',
    #         facecolor='none',
    #         transform=fig.transFigure,
    #         zorder=1000
    #     )
    # ])

    if configMap.titre_carte : 
        titre = configMap.titre_carte
        if configMap.titre_date:
            titre += ' ' + date_title
            plt.title(titre, fontsize=configMap.titre_fontsize, pad=configMap.titre_pad, backgroundcolor=configMap.titre_backgroundcolor)

    elif configMap.titre_date:
        titre = date_title
        plt.title(titre, fontsize=configMap.titre_fontsize, pad=configMap.titre_pad, backgroundcolor=configMap.titre_backgroundcolor)
    
    plt.savefig(full_png_path, dpi=300, bbox_inches='tight', pad_inches=0, facecolor=fig.get_facecolor())
    
    map_html = m._repr_html_()
    with open(full_html_path, "w", encoding="utf-8") as f:
        f.write(map_html)
    print('carte obs générée')
    return {
        'date_obs': date_title,
        'map': map_html,
        'png': public_png_path
    }

def generate_forecast_map(date_string, echeance,pk=None):

    date_fcst = datetime.strptime(date_string, "%Y-%m-%d")

    if pk is not None : 
        configMap = MapFcstConfiguration.objects.get(id=pk)
        identifier = pk
    else : 
        configMap = MapFcstConfiguration.objects.filter(active=True).first()
        identifier = configMap.id
    if not configMap:
        try:
            configMap, _ = MapFcstConfiguration.objects.update_or_create(active=True)
            configMap.save()
            zones = Zone.objects.filter(category='ville')
            configMap.zones.set(zones)
            identifier = 0
        except Exception:
            configMap = MapFcstConfiguration.objects.filter(name='Carte par defaut').first()
            identifier = 0
    
    data_fcst = Forecast.objects.filter(date=date_fcst, echeance=echeance, zone__in=configMap.zones.all())

    try:
        date_title = (date_fcst + timedelta(hours=int(echeance))).strftime("%A %d %B %Y %Hh00").capitalize()
    except Exception:
        name = Echeance.objects.filter(echeance=echeance).first().name
        date_title = date_fcst.strftime("%A %d %B %Y") + f" ({name})"

    png_file = f'{identifier}_fcst_map_{date_fcst.strftime("%d%m%Y")}_{echeance}.png'
    html_file = f'{identifier}_fcst_map_{date_fcst.strftime("%d%m%Y")}_{echeance}.html'

    output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'fcst_map', date_fcst.strftime("%Y/%m/%d"), 'png')
    output_path_html = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'fcst_map', date_fcst.strftime("%Y/%m/%d"), 'html')
    output_path_png_aff = os.path.join('/media', 'chartmet', 'fcst_map', date_fcst.strftime("%Y/%m/%d"), 'png', png_file)

    os.makedirs(output_path_png, exist_ok=True)
    os.makedirs(output_path_html, exist_ok=True)

    output_path_png = os.path.join(output_path_png, png_file)
    output_path_html = os.path.join(output_path_html, html_file)

    bfa_shape = cache_geometry(configMap.zip_file.file.path)
    union_geom = cache_union_geometry(configMap.zip_file.file.path)

    fig, ax = plt.subplots(figsize=(10, 8), facecolor=configMap.facecolor)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    bfa_shape.plot(ax=ax, color=configMap.color_shape, edgecolor=configMap.intern_edgecolor, linewidth=configMap.intern_linewidth)
    gpd.GeoSeries(union_geom).boundary.plot(ax=ax, edgecolor=configMap.border_edgecolor, linewidth=configMap.border_linewidth)

    m = folium.Map(location=[12.2383, -1.5616], zoom_start=7, min_zoom=7)
    marker_cluster = MarkerCluster().add_to(m)
    displayed_coords = []

    merged_geom_wkt = shapely_to_wkt(union_geom)
    merged_geom_django = GEOSGeometry(merged_geom_wkt)

    @lru_cache(maxsize=None)
    def load_icon(symb):
        symbole_name = f'{symb}.png'
        real_path = os.path.join(settings.MEDIA_ROOT, 'weathericons', symbole_name)
        return real_path, Image.open(real_path)

    fc = organize_fcst(data_fcst)
    for city, data in fc.items():
        x, y = city.geom.x, city.geom.y
        if not city.geom.within(merged_geom_django):
            continue
        tmin = strip_html(data.get('air_temperature_min', 'NP')) or 'NP'
        tmax = strip_html(data.get('air_temperature_max', 'NP')) or 'NP'
        rr = strip_html(data.get('precipitation_amount', '')) or ''
        symb = strip_html(data.get('symbol_code', 'np')) or 'np'

        icon_path, img = load_icon(symb)

        icon = folium.CustomIcon(icon_path, icon_size=(60, 60), icon_anchor=(20, 20))
        iframe = folium.IFrame(f"{city.name} :<br> {symb}<br>T :<span style='color:blue'>{tmin}</span>/<span style='color:red'>{tmax}</span>°C")
        popup = folium.Popup(iframe, min_width=150, max_width=200)
        folium.Marker([y, x], 
            icon=icon, 
            popup=popup, #f"{city.name} :\n {symb}\nT :{tmin}/{tmax}°C", 
            tooltip=city.name).add_to(marker_cluster
            )

        if not is_far_enough(x, y, displayed_coords, min_dist=configMap.min_dist / 100):
            continue

        ab = AnnotationBbox(OffsetImage(img, zoom=0.4), (x, y), frameon=False, pad=0)
        
        if configMap.temps_sensible : 
            ax.add_artist(ab)
        else : 
            plt.plot(x, y, marker='+', color='black', markersize=2)
            x -=0.15
        
        plt.text(x + 0.2, y, f"{city.name}\n", fontsize=7, bbox=dict(facecolor='white', alpha=0.2, edgecolor='none'))
        if configMap.tmin and configMap.tmax :
            plt.text(x + 0.2, y - 0.05, f"{tmin}", color='blue', fontweight='bold', fontsize=7) 
            plt.text(x + 0.2 + len(str(tmin)) * 0.07, y - 0.05, "/", fontsize=6)
            plt.text(x + 0.2 + len(str(tmin)) * 0.07 + 0.05, y - 0.05, f"{tmax}", color='red', fontweight='bold', fontsize=7)
        elif configMap.tmin and not configMap.tmax:
            plt.text(x + 0.2, y - 0.05, f"{tmin}", color='blue', fontweight='bold', fontsize=7)
        elif configMap.tmax and not configMap.tmin:
            plt.text(x + 0.2, y - 0.05, f"{tmax}", color='red', fontweight='bold', fontsize=7)
        if (configMap.tmin or configMap.tmax) and configMap.pluie :
            plt.text(x + 0.2, y - 0.15, f"{rr}", color='black', fontweight='bold', fontsize=6)
        elif configMap.pluie : 
            plt.text(x + 0.2, y - 0.05, f"{rr}", color='black', fontweight='bold', fontsize=6)

        displayed_coords.append((x, y))

    if configMap.logo :
        img_path = configMap.logo.file 
        logo = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = 0.05 * fig_height_in_pixels  # 5% de la hauteur
        logo_zoom = desired_logo_height / logo.shape[0]  # logo.shape[0] = hauteur en pixels de l'image
        imagebox = OffsetImage(logo, zoom=logo_zoom)
        ab = AnnotationBbox(imagebox, xy=(0.01, 0.01), xycoords='axes fraction',
                            frameon=False, box_alignment=(0, 0))  # coin haut gauche
        ax.add_artist(ab)

    if configMap.legende_1:
        img_path = configMap.legende_1.file 
        legende_1 = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = configMap.taille_legende_1/100 * fig_height_in_pixels  # % de la hauteur
        logo_zoom = desired_logo_height / legende_1.shape[0]  # Hauteur de l'image
        imagebox = OffsetImage(legende_1, zoom=logo_zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(0, 1),              
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(0, 1)          
        )
        ax.add_artist(ab)

    if configMap.legende_2:
        img_path = configMap.legende_2.file 
        legende_2 = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = configMap.taille_legende_2/100 * fig_height_in_pixels  # % de la hauteur
        logo_zoom = desired_logo_height / legende_2.shape[0]  # Hauteur de l'image
        imagebox = OffsetImage(legende_2, zoom=logo_zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(1, 0),              
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(1, 0)          # Alignement du coin bas droit de l'image
        )
        ax.add_artist(ab)

    if configMap.legende_3:
        img_path = configMap.legende_3.file 
        legende_3 = mpimg.imread(img_path)
        fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
        desired_logo_height = configMap.taille_legende_3/100 * fig_height_in_pixels  # % de la hauteur
        logo_zoom = desired_logo_height / legende_3.shape[0]  # Hauteur de l'image
        imagebox = OffsetImage(legende_3, zoom=logo_zoom)
        ab = AnnotationBbox(
            imagebox,
            xy=(1, 1),              
            xycoords='axes fraction',
            frameon=False,
            box_alignment=(1, 1)          # Alignement du coin haut droit de l'image
        )
        ax.add_artist(ab)



    ax.axis('off')
    # Ajouter un cadre autour de toute la figure
    # fig.patches.extend([
    #     patches.Rectangle(
    #         (0, 0),         # coin inférieur gauche en coordonnées normalisées
    #         1,              # largeur = 100% de la figure
    #         1,              # hauteur = 100% de la figure
    #         linewidth=2,
    #         edgecolor='gray',
    #         facecolor='none',
    #         transform=fig.transFigure,
    #         zorder=1000
    #     )
    # ])
    if configMap.titre_carte :
        titre = configMap.titre_carte
        if configMap.titre_date:
            titre += ' ' + date_title
            plt.title(titre, fontsize=configMap.titre_fontsize, pad=configMap.titre_pad, backgroundcolor=configMap.titre_backgroundcolor)

    elif configMap.titre_date:
        titre = date_title
        plt.title(titre, fontsize=configMap.titre_fontsize, pad=configMap.titre_pad, backgroundcolor=configMap.titre_backgroundcolor)
    
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight', pad_inches=0, facecolor=fig.get_facecolor())

    map_html = m._repr_html_()
    with open(output_path_html, "w", encoding="utf-8") as f:
        f.write(map_html)
    print('carte previ générée')
    return {'date_fcst': date_title, 'map': map_html, 'png': output_path_png_aff}

def generate_model_map(date_string, ech1,ech2,param,function='mean',pk=None,schema='gfs_model',table='weather_data'):
    date_run = datetime.strptime(date_string, "%Y-%m-%d")
    heure_run = "00"
    fromEch=int(ech1)
    toEch=int(ech2)
    if fromEch > toEch :
        fromEch=int(ech2)
        toEch=int(ech1)

    png_file = f'{pk}_map_model_{function}_{param}_{date_run.strftime("%d%m%Y")}_{fromEch}_{toEch}.png'

    output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'model_map',schema, date_run.strftime("%Y/%m/%d"), 'png')
    output_path_png_aff = os.path.join('/media', 'chartmet', 'model_map',schema, date_run.strftime("%Y/%m/%d"), 'png', png_file)
    os.makedirs(output_path_png, exist_ok=True)
    output_path_png = os.path.join(output_path_png, png_file)


    date_title = (date_run + timedelta(hours=fromEch)).strftime("%A %d %B").capitalize()
    date_title += " - " + (date_run + timedelta(hours=toEch)).strftime("%A %d %B %Y").capitalize()
    if True : #not os.path.isfile(output_path_png):
        try :
            import time
            start = time.time()
            df = get_previsions(fromEch,toEch,date_run,heure_run,schema,table)
            # df_sum = df.groupby(['lat', 'lon'])[param].mean().reset_index()
            df_sum = df.groupby(['lat', 'lon'])[param].agg(function).reset_index()
            df_sum.rename(columns={param: 'param'}, inplace=True)
            end = time.time()
            # print(f"Temps d'exécution : {end - start :.6f} secondes pour get prevision")
            start = time.time()
            if pk is not None : configMap = MapModelConfiguration.objects.get(id=pk)
            else : configMap = None
            start = time.time()
            map_delimite(df_sum,output_path_png,param=param,configMap=configMap,date_titre=date_title)
            end = time.time()
            # print(f"Temps d'exécution : {end - start :.6f} secondes pour genration map delimit")

        except Exception as e :
            print(e)

    return {'date_fcst': date_title, 'png': output_path_png_aff}

import calendar
import datetime as dt

def format_decade_title(decade_info):
    day = decade_info['start_date'].day
    month = calendar.month_name[decade_info['start_date'].month]
    year = decade_info['start_date'].year

    if day <= 10:
        label = "1ère décade"
    elif day <= 20:
        label = "2e décade"
    else:
        label = "3e décade"

    return label, month, year
def decade_title(decadeInfo1,decadeInfo2, function=''):
    dec1_label, dec1_month, dec1_year = format_decade_title(decadeInfo1)
    dec2_label, dec2_month, dec2_year = format_decade_title(decadeInfo2)

    if decadeInfo1['start_date'] == decadeInfo2['start_date']:
        # Même décade : on affiche label + mois + année
        date_title = f"{dec1_label} {dec1_month} {dec1_year}"
    else:
        if dec1_year != dec2_year:
            # Années différentes, on affiche année en premier pour chaque
            date_title = f"{function}{dec2_year} {dec2_label} {dec2_month} / {dec1_year} {dec1_label} {dec1_month}"
        else:
            # Même année, on affiche année une fois après
            date_title = f"{function}{dec2_label} {dec2_month} / {dec1_label} {dec1_month} {dec1_year}"
    return date_title
def get_decade_from_offset(date_ref, offset=0):
    # Identifier la décade actuelle
    day = date_ref.day
    month = date_ref.month
    year = date_ref.year

    if day <= 10:
        current_decade = 1
    elif day <= 20:
        current_decade = 2
    else:
        current_decade = 3


    # Position absolue dans une "timeline" de décades
    total_decade_index = (year * 12 + (month - 1)) * 3 + (current_decade - 1) + offset

    # Recalculer année, mois, et décade à partir de l’indice total
    new_year = total_decade_index // (12 * 3)
    rest = total_decade_index % (12 * 3)
    new_month = rest // 3 + 1
    new_decade = rest % 3 + 1

    # Calcul de la date de début et fin de la décade
    if new_decade == 1:
        start_day = 1
        end_day = 10
    elif new_decade == 2:
        start_day = 11
        end_day = 20
    else:
        start_day = 21
        end_day = calendar.monthrange(new_year, new_month)[1]

    start_date = dt.date(new_year, new_month, start_day)
    end_date = dt.date(new_year, new_month, end_day)

    return {
        'year': new_year,
        'month': new_month,
        'decade': new_decade,
        'start_date': start_date,
        'end_date': end_date,
    }
def toMultiPolygone(shapes):
    from shapely.geometry import MultiPolygon, Polygon
    all_polygons = []
    for shape in shapes:
        if isinstance(shape, Polygon):
            all_polygons.append(shape)
        elif isinstance(shape, MultiPolygon):
            all_polygons.extend(shape.geoms)

    # Créer un MultiPolygon à partir de la liste aplatie
    multipolygon = MultiPolygon(all_polygons)
    return multipolygon
def load_config(config_path=CONFIG_PATH):
    current_dir = os.path.dirname(__file__)  # répertoire où se trouve obswise.py
    config_path = os.path.join(current_dir, config_path)
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_db_connection(db_config):
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password']
    )

def get_previsions(from_ech, to_ech, date_run, heure_run, schema='gfs_model', table='weather_data'):
    config = load_config()
    db_config = config.get("database")

    query = f"""
        SELECT lat, long, ech, data
        FROM {schema}.{table}
        WHERE ech BETWEEN %s AND %s AND date = %s AND cycle = %s
        ORDER BY ech
    """

    try:
        with get_db_connection(db_config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, (from_ech, to_ech, date_run, heure_run))
                rows = cur.fetchall()
    except Exception as e:
        print(f"Error occurred: {e}")
        return pd.DataFrame()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Éclatement du champ JSON "data" en colonnes
    data_expanded = pd.json_normalize(df['data'])

    # Fusion avec les autres colonnes utiles
    df_final = pd.concat([df.drop(columns='data'), data_expanded], axis=1)

    # Renommer les colonnes pour cohérence
    df_final.rename(columns={'long': 'lon', 'ech': 'step'}, inplace=True)

    return df_final
def get_previsions_old(fromEch,toEch,date_run,heure_run,schema='gfs_model',table='weather_data'):
    config = load_config()
    db_config = config.get("database")
    rows = {}
    conn = get_db_connection(db_config)
    cur = conn.cursor() #(cursor_factory=RealDictCursor)
    sql = """
        SELECT lat,long, ech, data
        FROM %s.%s
        WHERE ech BETWEEN %d AND %d AND date='%s' AND cycle='%s' order by ech
    """ % (schema,table,fromEch,toEch,date_run,heure_run)    
    try:
        cur.execute(sql)
        rows = cur.fetchall()  # Liste de dictionnaires
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        cur.close()
        conn.close()
    df = pd.DataFrame([
        {'lat': lat, 'lon': lon, 'step': step, **params}
        for lat, lon, step, params in rows
    ])
    return df

def map_delimite(df, file_name, param=None, configMap=None,date_titre=None):
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from scipy.interpolate import griddata, Rbf
    from shapely.geometry import MultiPolygon, Polygon, Point
    from cartopy.io.shapereader import Reader
    from matplotlib.patches import PathPatch
    from django.conf import settings
    import zipfile
    import matplotlib.colors as mcolors

    # --- Grille régulière ---
    lon = df['lon']
    lat = df['lat']
    valeurs = df['param']

    if configMap and configMap.extrapolate :
        min_lon, max_lon = -5.5, 2.5
        min_lat, max_lat = 9.0, 15.5
        lon_grid = np.linspace(min_lon, max_lon, 200)
        lat_grid = np.linspace(min_lat, max_lat, 200)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        # rbf = Rbf(lon, lat, valeurs, function=configMap.extrapolation_method if configMap else 'cubic')
        # valeurs_grid = rbf(lon_mesh, lat_mesh)
        if configMap.extrapolation_method == 'kriging':
            from pykrige.ok import OrdinaryKriging
            param_vario={}
            if configMap.vario_nugget :
                param_vario['nugget'] = configMap.vario_nugget
            if configMap.vario_sill :
                param_vario['sill'] = configMap.vario_sill
            if configMap.vario_range :
                param_vario['range'] = configMap.vario_range
            if len(param_vario) == 0 : param_vario=None
            pprint(param_vario)
            OK = OrdinaryKriging(lon, lat, valeurs, variogram_model=configMap.variogram_model if configMap.variogram_model else 'spherical',variogram_parameters=param_vario)
            valeurs_grid, ss = OK.execute('grid', lon_mesh[0], lat_mesh[:, 0])
        else:
            rbf = Rbf(lon, lat, valeurs, function=configMap.extrapolation_method if configMap else 'cubic')
            valeurs_grid = rbf(lon_mesh, lat_mesh)
    elif configMap and configMap.interpolate:
        lon_grid = np.linspace(lon.min(), lon.max(), 200)
        lat_grid = np.linspace(lat.min(), lat.max(), 200)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        # valeurs_grid = griddata((lon, lat), valeurs, (lon_mesh, lat_mesh), method=configMap.interpolation_method if configMap else 'cubic')
        if configMap.interpolation_method == 'kriging':
            from pykrige.ok import OrdinaryKriging
            OK = OrdinaryKriging(lon, lat, valeurs, variogram_model=configMap.variogram_model if configMap.variogram_model else 'spherical')
            valeurs_grid, ss = OK.execute('grid', lon_mesh[0], lat_mesh[:, 0])
        else:
            valeurs_grid = griddata((lon, lat), valeurs, (lon_mesh, lat_mesh), method=configMap.interpolation_method if configMap else 'cubic')
    else :
        lon_grid = np.linspace(lon.min(), lon.max(), 200)
        lat_grid = np.linspace(lat.min(), lat.max(), 200)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        valeurs_grid = griddata((lon, lat), valeurs, (lon_mesh, lat_mesh), method=configMap.interpolation_method if configMap else 'cubic')
    
    
    # --- Chargement du shapefile ---
    shapefile_zip_path = configMap.zip_file.file.path if configMap else os.path.join(settings.MEDIA_ROOT, 'shapefiles/provinces.zip')
    with zipfile.ZipFile(shapefile_zip_path, 'r') as zip_ref:
        shp_files = [f for f in zip_ref.namelist() if f.endswith('.shp')]
        if not shp_files:
            raise ValueError("Aucun fichier .shp trouvé dans le fichier ZIP.")
        shapefile_inside_zip = shp_files[0]  # prendre le premier .shp trouvé
    
    
    reader = Reader(f"zip://{shapefile_zip_path}!{shapefile_inside_zip}")
    shapes = list(reader.geometries())
    multipolygon = toMultiPolygone(shapes)

    # --- Bounding box ---
    # minx, miny, maxx, maxy = multipolygon.bounds

    # --- Bounding box ---
    minx, miny, maxx, maxy = multipolygon.bounds

    # Ajout d'une marge personnalisable (optionnel)
    if configMap and hasattr(configMap, 'margin_factor'):
        margin_factor = configMap.margin_factor  # Par exemple 0.05 pour 5% de marge
    else:
        margin_factor = 0.02  # Marge par défaut très petite (2%)

    # Calcul des marges
    width = maxx - minx
    height = maxy - miny
    margin_x = width * margin_factor
    margin_y = height * margin_factor

    # Application des marges
    minx_adj = minx - margin_x
    maxx_adj = maxx + margin_x
    miny_adj = miny - margin_y
    maxy_adj = maxy + margin_y


    # --- Masquage ---
    from shapely.vectorized import contains
    mask = ~contains(multipolygon, lon_mesh, lat_mesh)
    valeurs_masked = np.ma.array(valeurs_grid, mask=mask)
    # --- Création de la carte ---
    
    fig, ax = plt.subplots(figsize=(configMap.largeur if configMap else 6.4, configMap.hauteur if configMap else 6.4), facecolor=configMap.facecolor if configMap else 'white', subplot_kw={'projection': ccrs.PlateCarree()})
    
    class_labels = False
    if configMap and configMap.legend :
        levels,cmap,norm,class_labels = configMap.legend.get_cmap()
        title_legend = configMap.legend.title

    else :
        vmin = np.nanmin(valeurs_masked)
        vmax = np.nanmax(valeurs_masked)
        if vmin == vmax:
            epsilon = 0.1 if vmax == 0 else abs(vmax * 0.01)  # petite marge
            levels = [vmin - epsilon, vmax + epsilon]
        else:
            try :
                levels = np.linspace(vmin, vmax, num=10)
                levels = [round(l,1) for l in levels]
            except :
                levels = np.linspace(valeurs_grid.min(), valeurs_grid.max(), num=10)
                levels = [round(l,1) for l in levels]
        cmap = plt.get_cmap(configMap.cmap if configMap else 'viridis', len(levels)-1)
        norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
        title_legend = 'Valeurs'
    cf = None
    try : 
        if configMap :
            if not configMap.interpolate and not configMap.extrapolate:
                lon_grid = np.linspace(lon.min(), lon.max(), 200)
                lat_grid = np.linspace(lat.min(), lat.max(), 200)

                mask = ~contains(multipolygon, lon, lat)

                cell_width_deg = lon_grid[1] - lon_grid[0]
                cell_height_deg = lat_grid[1] - lat_grid[0]
                taille_en_points = (cell_width_deg * 111)**2.96
                sc = ax.scatter(
                    lon[~mask],
                    lat[~mask],
                    c=valeurs[~mask],
                    cmap=configMap.cmap if configMap else 'viridis',
                    s=taille_en_points,
                    marker='s',
                    edgecolors='none',
                    transform=ccrs.PlateCarree()
                )
            else :
                if configMap.show_color_fill:
                    # cf = ax.contourf(lon_mesh, lat_mesh, valeurs_masked, levels=levels, cmap=cmap, extend='both')
                    cf = ax.contourf(lon_mesh, lat_mesh, valeurs_masked, levels=levels, cmap=cmap, norm=norm, extend='max')
                if configMap.show_contour_lines:
                    cs = ax.contour(lon_mesh, lat_mesh, valeurs_masked, levels=levels, 
                        colors=configMap.contour_edgecolor if configMap else 'black', 
                        linewidths=configMap.contour_linewidths if configMap else 0.8)
                    ax.clabel(cs, inline=True, fontsize=configMap.contour_labelsize if configMap else 5, fmt='%1.0f')
            if configMap.logo :
                img_path = configMap.logo.file 
                logo = mpimg.imread(img_path)
                fig_height_in_pixels = fig.get_size_inches()[1] * fig.dpi
                desired_logo_height = 0.05 * fig_height_in_pixels  # 5% de la hauteur
                logo_zoom = desired_logo_height / logo.shape[0]  # logo.shape[0] = hauteur en pixels de l'image
                imagebox = OffsetImage(logo, zoom=logo_zoom)
                ab = AnnotationBbox(imagebox, xy=(0.01, 0.99), xycoords='axes fraction',
                                    frameon=False, box_alignment=(0, 1))  # coin haut gauche
                ax.add_artist(ab)
        else :
            cf = ax.contourf(lon_mesh, lat_mesh, valeurs_masked, levels=levels, cmap=cmap, extend='max')
    except ValueError as e:
        print('Error : carte non générée')
        print(e)
        pass

    bfa_shape = cache_geometry(shapefile_zip_path)
    union_geom = cache_union_geometry(shapefile_zip_path)
    # bfa_shape = gpd.read_file(shapefile_zip_path)
    bfa_shape.plot(ax=ax, facecolor='none',edgecolor=configMap.intern_edgecolor if configMap else 'gray', linewidth=configMap.intern_linewidth  if configMap else 0.6)
    gpd.GeoSeries(union_geom).boundary.plot(ax=ax, edgecolor=configMap.border_edgecolor  if configMap else 'black', linewidth=configMap.border_linewidth if configMap else 0.8)

    # ax.set_extent([minx, maxx, miny, maxy], crs=ccrs.PlateCarree())
    # ax.set_xticks(np.arange(np.floor(minx), np.ceil(maxx)+0.5, 0.5), crs=ccrs.PlateCarree())
    # ax.set_yticks(np.arange(np.floor(miny), np.ceil(maxy)+0.5, 0.5), crs=ccrs.PlateCarree())

    ax.set_extent([minx_adj, maxx_adj, miny_adj, maxy_adj], crs=ccrs.PlateCarree())
     # Ajustez aussi les ticks pour qu'ils correspondent à la nouvelle étendue
    tick_spacing = 1.0  # ou une valeur adaptée à votre échelle
    ax.set_xticks(np.arange(np.floor(minx_adj), np.ceil(maxx_adj)+tick_spacing, tick_spacing), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(np.floor(miny_adj), np.ceil(maxy_adj)+tick_spacing, tick_spacing), crs=ccrs.PlateCarree())
    ################################
    ax.tick_params(labelsize=6)
    ax.gridlines(draw_labels=False, linewidth=0.2)

    if configMap and cf:
        if configMap.show_color_fill:
            cbar = plt.colorbar(cf, ax=ax, orientation=configMap.orientation_palette if configMap else 'horizontal', shrink=0.75, pad=0.05, ticks=levels)
            cbar.set_label(title_legend, fontsize=6)
            cbar.ax.tick_params(labelsize=6)
            
            if class_labels : cbar.set_ticklabels(class_labels)
            else : 
                if len(str(levels[0])) > 3:
                    cbar.set_ticks(levels[::2])

    if configMap and configMap.titre_carte :
        titre = configMap.titre_carte
        plt.suptitle(titre, fontsize=configMap.titre_fontsize, backgroundcolor=configMap.titre_backgroundcolor, y=0.93)
        
    if configMap and configMap.titre_date:
        ax.set_title(date_titre,fontsize=6)
    ##### Ajout des localités 
    if configMap and configMap.localites:
        villes = configMap.localites.all()
        # merged_geom = bfa_shape.unary_union
        merged_geom_wkt = shapely_to_wkt(union_geom)
        merged_geom_django = GEOSGeometry(merged_geom_wkt)

        for ville in villes:
            if not ville.geom.within(merged_geom_django):
                continue
            ax.plot(ville.geom.x, ville.geom.y, marker=configMap.symbole, color=configMap.couleur_symbole, markersize=configMap.symbole_size, transform=ccrs.PlateCarree())
            ax.text(ville.geom.x + 0.05, ville.geom.y, ville.name,color=configMap.couleur_text,fontsize=configMap.text_labelsize, transform=ccrs.PlateCarree())
     ##### Ajout des stations 
    if configMap and configMap.stations:
        stations = configMap.stations.all()
        # merged_geom = bfa_shape.unary_union
        merged_geom_wkt = shapely_to_wkt(union_geom)
        merged_geom_django = GEOSGeometry(merged_geom_wkt)

        for stat in stations:
            if not stat.geom.within(merged_geom_django):
                continue
            ax.plot(stat.geom.x, stat.geom.y, marker=configMap.symbole_station, color=configMap.couleur_symbole_station, markersize=configMap.symbole_size_station, transform=ccrs.PlateCarree())
            ax.text(stat.geom.x + 0.05, stat.geom.y, stat.name,color=configMap.couleur_text_station,fontsize=configMap.text_labelsize_station, transform=ccrs.PlateCarree())

    plt.savefig(file_name, dpi=300, pad_inches=0, bbox_inches='tight')
    
    plt.close()
    print("Carte générée avec succès")

def get_parameters(schema='gfs_model',table='weather_parameter_mapping'):
    config = load_config()
    db_config = config.get("database")
    rows = {}
    conn = get_db_connection(db_config)
    cur = conn.cursor() #(cursor_factory=RealDictCursor)
    sql = """ SELECT parameter_name, grib_variable, grib_level, parameter_description, origin_unit, unit FROM %s.%s
            where parameter_status='on'
            """ % (schema,table)
    try:
        cur.execute(sql)
        rows = cur.fetchall()  # Liste de dictionnaires
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        cur.close()
        conn.close()

    df = pd.DataFrame([
        { 'parameter_name':parameter_name, 'grib_variable':grib_variable, 'grib_level':grib_level, 'parameter_description':parameter_description, 'origin_unit':origin_unit, 'unit':unit}
        for parameter_name, grib_variable, grib_level,parameter_description, origin_unit, unit in rows
    ])
    return df

def get_functions(schema='gfs_model',table='functions'):
    config = load_config()
    db_config = config.get("database")
    rows = {}
    conn = get_db_connection(db_config)
    cur = conn.cursor() #(cursor_factory=RealDictCursor)
    sql = """ SELECT name, function FROM %s.%s
            where status IS TRUE
            """ % (schema,table)
    try:
        cur.execute(sql)
        rows = cur.fetchall()  # Liste de dictionnaires
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        cur.close()
        conn.close()

    df = pd.DataFrame([
        { 'name':name, 'function':function,}
        for name, function in rows
    ])
    return df

def get_parameters_decade(schema='climat',table='parameters_decades'):
    config = load_config()
    db_config = config.get("database")
    rows = {}
    conn = get_db_connection(db_config)
    cur = conn.cursor() #(cursor_factory=RealDictCursor)
    sql = """ SELECT parameter FROM %s.%s
            """ % (schema,table)
    try:
        cur.execute(sql)
        rows = cur.fetchall()  # Liste de dictionnaires
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        cur.close()
        conn.close()

    df = pd.DataFrame([
        { 'parameter':parameter_name}
        for parameter_name in rows
    ])
    return df


def generate_points_map(date_string,localites,param,echeance,pk=None):
    date_obs = datetime.strptime(date_string, "%Y-%m-%d")
    iid = pk 
    if not iid : iid = 0
    png_file = f'{iid}_map_points_{localites.id}_{param.name}_{date_obs.strftime("%d%m%Y")}_{echeance.echeance}.png'

    output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'points_map',date_obs.strftime("%Y/%m/%d"), 'png')
    output_path_png_aff = os.path.join('/media', 'chartmet', 'points_map', date_obs.strftime("%Y/%m/%d"), 'png', png_file)
    os.makedirs(output_path_png, exist_ok=True)
    output_path_png = os.path.join(output_path_png, png_file)


    date_title = (date_obs + timedelta(hours=int(echeance.start))).strftime("%A %d %B").capitalize()
    date_title += " - " + (date_obs + timedelta(hours=int(echeance.end))).strftime("%A %d %B %Y").capitalize()
    stations = localites.stations.all()
    obs = Observation.objects.filter(date=date_string,parametre=param,heure=echeance.echeance,station__in=stations)
    data = []
    for o in obs :
        try :
            text = BeautifulSoup(o.observation, "html.parser").get_text(strip=True)
            valeur = float(text)
            data.append({'lat':o.station.geom.y,'lon':o.station.geom.x,'param':valeur})
        except Exception as e:
            print(e)
            continue
    df = pd.DataFrame(data)
    if True : #not os.path.isfile(output_path_png):
        try :
            if pk is not None : configMap = MapModelConfiguration.objects.get(id=pk)
            else : configMap = None
            # configMap = MapModelConfiguration.objects.get(name='Carte BF')
            map_delimite(df,output_path_png,param=param,configMap=configMap,date_titre=date_title)
        except Exception as e :
            print(e)

    return {'date_fcst': date_title, 'png': output_path_png_aff}

def generate_Spatial_points_map(date_string,localites,pk=None):
    date_obs = datetime.strptime(date_string, "%Y-%m-%d")
    stations = localites.stations.all()


    if True : #not os.path.isfile(output_path_png):
        try :
            if pk is not None : configMap = MapSpatialConfiguration.objects.get(id=pk)
            else : configMap = MapSpatialConfiguration.objects.create()
            
            param=configMap.parametre
            echeance = configMap.echeance
            
            obs = Observation.objects.filter(date=date_string,parametre__id=param.id,heure=echeance.echeance)

            png_file = f'{configMap.id}_Preconfigured_map_points_{localites.id}_{param.name}_{date_obs.strftime("%d%m%Y")}_{echeance.echeance}.png'

            output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'points_map',date_obs.strftime("%Y/%m/%d"), 'png')
            output_path_png_aff = os.path.join('/media', 'chartmet', 'points_map', date_obs.strftime("%Y/%m/%d"), 'png', png_file)
            os.makedirs(output_path_png, exist_ok=True)
            output_path_png = os.path.join(output_path_png, png_file)
            date_title = (date_obs + timedelta(hours=int(echeance.start))).strftime("%A %d %B").capitalize()
            date_title += " - " + (date_obs + timedelta(hours=int(echeance.end))).strftime("%A %d %B %Y").capitalize()


            data = []
            for o in obs :
                try :
                    text = BeautifulSoup(o.observation, "html.parser").get_text(strip=True)
                    valeur = float(text)
                    data.append({'lat':o.station.geom.y,'lon':o.station.geom.x,'param':valeur})
                except Exception as e:
                    print(e)
                    continue
            df = pd.DataFrame(data)
            map_delimite(df,output_path_png,param=param,configMap=configMap,date_titre=date_title)
        except Exception as e :
            print(e)
            return {'date_fcst': date_obs, 'png': '','error':'Erreur'}

    return {'date_fcst': date_title, 'png': output_path_png_aff}

def get_decadeData_from_db(date_bult, decade,param, source, table='decades', schema='climat'):
    config = load_config()
    db_config = config.get("database")

    decadeInfo= get_decade_from_offset(date_bult,decade) 
    query = f"""
        SELECT id,lat, lon, value
        FROM {schema}.{table}
        WHERE decade=%s AND month=%s AND year=%s AND parameter=%s AND source=%s
        ORDER BY id
    """
    # pprint(query%(decadeInfo['decade'], decadeInfo['month'], decadeInfo['year'], param,source))
    try:
        with get_db_connection(db_config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, (decadeInfo['decade'], decadeInfo['month'], decadeInfo['year'], param,source))
                rows = cur.fetchall()
    except Exception as e:
        print(f"Error occurred: {e}")
        return pd.DataFrame()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df

def generate_Decadaire_map(date_string,decade1,decade2,source,parametre,fonction, func_name='',pk=None,interpolation="",extrapolation="",variogramme="",param_variogramme=""):
    date_obs = datetime.strptime(date_string, "%Y-%m-%d")
    decadeInfo1= get_decade_from_offset(date_obs,decade1)
    qs1 = ClimatDecades.objects.filter(decade=decadeInfo1['decade'],month=decadeInfo1['month'],year=decadeInfo1['year'],parameter=parametre,source=source)
    df1 = pd.DataFrame.from_records(qs1.values())

    decadeInfo2= get_decade_from_offset(date_obs,decade2)
    qs2 = ClimatDecades.objects.filter(decade=decadeInfo2['decade'],month=decadeInfo2['month'],year=decadeInfo2['year'],parameter=parametre,source=source)
    df2 = pd.DataFrame.from_records(qs2.values())

    df1_renamed = df1.rename(columns={'value': 'value1'})
    df2_renamed = df2.rename(columns={'value': 'value2'})
    try :
        # Fusion sur latitude et longitude
        df = pd.merge(df1_renamed[['lat', 'lon', 'value1']],
                          df2_renamed[['lat', 'lon', 'value2']],
                          on=['lat', 'lon'])

        # Calcul de la différence
        if fonction=='diff' :
            df['param'] = df['value1'] - df['value2']
        else :
            df['param'] = df[['value1', 'value2']].apply(fonction, axis=1)
    except Exception as e :
        print(f"---------")
        pprint(decadeInfo1)
        pprint(qs1)
        print(f"---------")
        pprint(decadeInfo2)
        pprint(qs2)
        print(f'Error : données indisponibles {e}')
        return {'date_fcst': 'Carte non disponible', 'png': ''}

    decadeInfo1= get_decade_from_offset(date_obs,decade1)
    decadeInfo2= get_decade_from_offset(date_obs,decade2)
    if func_name !='' :
        func_name = f"{func_name} : "
    date_title = decade_title(decadeInfo1,decadeInfo2,func_name) 
    # decadeInfo1['start_date'].strftime("%d%m%Y") + ' - ' + decadeInfo1['end_date'].strftime("%d%m%Y") 
    # date_title += " / " + decadeInfo2['start_date'].strftime("%d%m%Y") + ' - ' + decadeInfo2['end_date'].strftime("%d%m%Y")
    png_file = f'{pk}_map_decade_{source}_{parametre}_{fonction}_{decade1}_{decade2}_{date_obs.strftime("%d%m%Y")}.png'
    output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'decades',date_obs.strftime("%Y/%m/%d"), 'png')
    output_path_png_aff = os.path.join('/media', 'chartmet', 'decades', date_obs.strftime("%Y/%m/%d"), 'png', png_file)
    output_path_png_save = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'decades', date_obs.strftime("%Y/%m/%d"), 'png', png_file)

    os.makedirs(output_path_png, exist_ok=True)
            
    if True : #not os.path.isfile(output_path_png):
        try :
            if pk is not None : configMap = MapModelConfiguration.objects.get(id=pk)
            else : 
                configMap = None
                pk=0
            # configMap = MapModelConfiguration.objects.get(name='Carte BF')
            if interpolation != "" : 
                configMap.interpolate = True
                configMap.interpolation_method = interpolation
            else :
                configMap.interpolate = False
            if extrapolation != "" : 
                configMap.extrapolate = True
                configMap.extrapolation_method = extrapolation
            else :
                configMap.extrapolate = False
            if variogramme != "" : configMap.variogram_model = variogramme
            if param_variogramme != "" : 
                configMap.vario_nugget = param_variogramme['nugget']
                configMap.vario_range = param_variogramme['range']
                configMap.vario_sill = param_variogramme['sill']
            if configMap is not None:
                configMap.save()
            map_delimite(df,output_path_png_save,param=parametre,configMap=configMap,date_titre=date_title)
        except Exception as e :
            print(e)
            return {'date_fcst': date_obs, 'png': '','error':'Erreur'}
    return {'date_fcst': date_title, 'png': output_path_png_aff}

def generate_ClimMonth_map(from_year, from_month,to_year,to_month,param,source='ecmf',function='mean',pk=None):
    # clim_queryset = ClimatMois.objects.filter(
    #     Q(year__gt=from_year, year__lt=to_year) |
    #     Q(year=from_year, month__gte=from_month) |
    #     Q(year=to_year, month__lte=to_month),
    #     parameter=param,
    #     source=source
    # )
    from_month_total = from_year * 12 + from_month
    to_month_total = to_year * 12 + to_month

    # Annoter chaque ligne avec son "mois absolu"
    from django.db.models import F, IntegerField, ExpressionWrapper

    clim_queryset = ClimatMois.objects.annotate(
        month_total=ExpressionWrapper(F('year') * 12 + F('month'), output_field=IntegerField())
    ).filter(
        month_total__gte=from_month_total,
        month_total__lte=to_month_total,
        parameter=param,
        source=source
    )
    df = pd.DataFrame.from_records(
        clim_queryset.values(
            'station', 'lon', 'lat', 'month', 'year',
            'parameter', 'name', 'value', 'source'
        )
    )
    pprint(df)
    png_file = f'{pk}_map_monthClim_{function}_{param}_{source}_{from_month:02d}-{from_year}_to_{to_month:02d}-{to_year}.png'
    date_title = f"{from_month:02d}-{from_year} à {to_month:02d}-{to_year}"

    output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'climat','month', 'png')
    output_path_png_aff = os.path.join('/media', 'chartmet', 'climat','month', 'png', png_file)
    os.makedirs(output_path_png, exist_ok=True)
    output_path_png = os.path.join(output_path_png, png_file)
    if True : #not os.path.isfile(output_path_png):
        try :
            # import time
            # start = time.time()
            df_sum = df.groupby(['lat', 'lon'])['value'].agg(function).reset_index()
            df_sum.rename(columns={'value': 'param'}, inplace=True)
            # end = time.time()
            # print(f"Temps d'exécution : {end - start :.6f} secondes pour get prevision")
            # start = time.time()
            if pk is not None : configMap = MapModelConfiguration.objects.get(id=pk)
            else : configMap = None
            # start = time.time()
            map_delimite(df_sum,output_path_png,param=param,configMap=configMap,date_titre=date_title)
            # end = time.time()
            # print(f"Temps d'exécution : {end - start :.6f} secondes pour genration map delimit")

        except Exception as e :
            print(e)
    return {'date_fcst': date_title, 'png': output_path_png_aff}



