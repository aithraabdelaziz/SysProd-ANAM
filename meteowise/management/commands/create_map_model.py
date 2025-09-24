from django.utils import timezone
from datetime import datetime,timedelta
import os
import sys
# import yaml
import django
import pandas as pd
import numpy as np

import requests
from concurrent.futures import ThreadPoolExecutor
import time
import json

from pprint import pprint
from scipy.stats import mode


from forecast.models import Variable,Forecast,Zone
# from observation.models import Observation, Station
from django.db import transaction

import yaml

import psycopg2
from psycopg2.extras import RealDictCursor
import math

from django.conf import settings

main_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(main_folder_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "climforge.settings.dev")
django.setup()
from forecast.models import Variable, Forecast, Zone
from observation.models import Station, Observation
from bulletins.models import  Echeance
from django.db import transaction
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from collections import defaultdict

CONFIG_PATH = 'config.yaml'

VARIABLES = [
            {"name": "Minimum Air Temperature", "sn": "air_temperature_min", "unit": "°C",'cat':'value'},
            {"name": "Maximum Air Temperature", "sn": "air_temperature_max", "unit": "°C",'cat':'value'},
            {"name": "Pluie", "sn": "precipitation_amount", "unit": "mm",'cat':'value'},
            {'name':'Pression','sn':'air_pressure_at_sea_level','unit':'hPa','cat':'value'},
            {'name':'Direction','sn':'wind_from_direction','unit':'°','cat':'value'},
            {'name':'Force','sn':'wind_speed','unit':'km/h','cat':'value'},
            {"name": "Conditions", "sn": "symbol_code", "unit": "",'cat':'class'},
            {"name": "Humidité", "sn": "relative_humidity", "unit": "%",'cat':'value'},
            {"name": "Temps sensible", "sn": "symbol_code", "unit": "",'cat':'class'}

        ]

class Command(BaseCommand):
    help = ('Get the weather forecast from FGS model'
            'for all cities in the database and save it to the database.')

    def handle(self, *args, **options):
        nb_jour = 5
        date_retention = timezone.now() - timedelta(days=nb_jour)
        prevsions_a_supprimer = Forecast.objects.filter(date__lt=date_retention)
        prevsions_a_supprimer.delete()
        print("prévisions antérieur à "+date_retention.strftime("%d-%m-%Y")+" supprimées---------------")

        # cities = Zone.objects.filter(category='ville')
        fromEch=1
        toEch=168
        date_run=timezone.now().strftime("%Y-%m-%d")
        heure_run = "00"

        req2 = """
            SELECT lat,long, ech, data
            FROM gfs_model.weather_data
            WHERE ech BETWEEN %d AND %d AND date='%s' AND cycle='%s' order by ech
        """ % (fromEch,toEch,date_run,heure_run)

        rows = self.get_previsions(req2)
        df = pd.DataFrame([
            {'lat': lat, 'lon': lon, 'step': step, **params}
            for lat, lon, step, params in rows
        ])
        df_sum = df.groupby(['lat', 'lon'])['TMP'].mean().reset_index()
        df_sum.rename(columns={'TMP': 'param'}, inplace=True)
        # self.create_map(df_sum)
        # self.CPT_map(df_sum)
        self.map_delimite(df_sum)
        # results[city] = pd.DataFrame([
        #     {'ech': ech, **vars_dict} for ech, vars_dict in rows
        # ])

        # ech = Echeance.objects.get(echeance="12 next 24h")
        # for c,data in results.items():
        #     print(f'---------{c}')
        #     for nmv in VARIABLES:
        #         vv=Variable.objects.get(shortName=nmv['sn'])
        #         prev_desc = self.fcst_wise(nmv['sn'],data)
        #         if prev_desc!="":
        #             print('*******',end='')
        #             print(nmv['sn'], end=" : ")
        #             print(prev_desc, end="; ")

        #     print('')
        quit()

    def map_delimite(self, df):
        import os
        import numpy as np
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        from scipy.interpolate import griddata
        from shapely.geometry import MultiPolygon, Polygon, Point
        from cartopy.io.shapereader import Reader
        from matplotlib.patches import PathPatch

        
        # --- Grille régulière ---
        lon = df['lon']
        lat = df['lat']
        valeurs = df['param']
        lon_grid = np.linspace(lon.min(), lon.max(), 200)
        lat_grid = np.linspace(lat.min(), lat.max(), 200)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        valeurs_grid = griddata((lon, lat), valeurs, (lon_mesh, lat_mesh), method='cubic')

        # --- Chargement du shapefile ---
        shapefile_zip_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles/provinces.zip')
        shapefile_inside_zip = "provinces.shp"
        reader = Reader(f"zip://{shapefile_zip_path}!{shapefile_inside_zip}")
        shapes = list(reader.geometries())

        multipolygon = self.toMultiPolygone(shapes)

        # --- Calcul de la bounding box manuellement ---
        minx, miny, maxx, maxy = multipolygon.bounds  # (minx, miny, maxx, maxy)

        # --- Masque des données en dehors du shapefile ---
        mask = np.array([
            not multipolygon.contains(Point(x, y)) for x, y in zip(lon_mesh.ravel(), lat_mesh.ravel())
        ]).reshape(lon_mesh.shape)
        valeurs_masked = np.ma.array(valeurs_grid, mask=mask)

        # --- Palette CPT style ---
        levels = np.linspace(np.nanmin(valeurs_masked), np.nanmax(valeurs_masked), 16)

        levels = [round(l,1) for l in levels]

        cmap = plt.cm.get_cmap("gist_rainbow", len(levels)-1)

        # --- Création de la carte ---
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': ccrs.PlateCarree()})
        cf = ax.contourf(lon_mesh, lat_mesh, valeurs_masked, levels=levels, cmap=cmap, extend='both')

        # --- Ajout des frontières du shapefile ---
        ax.add_geometries(shapes, crs=ccrs.PlateCarree(), edgecolor='red', facecolor='none', linewidth=0.5)

        # --- Limite exacte de la carte = shapefile ---
        ax.set_extent([minx, maxx, miny, maxy], crs=ccrs.PlateCarree())

        # --- Ajout des stations (optionnel) ---
        stations = {
            "OUAGADOUGOU AERO": (-1.51, 12.35),
            "BOGANDÉ": (0.15, 13.5),
            "FADA N'GOURMA": (0.35, 12.05),
            "DORI": (0.03, 14.03),
            "PO": (-1.15, 11.15)
        }
        for name, (x, y) in stations.items():
            ax.text(x, y, name, fontsize=5, ha='center', va='center', transform=ccrs.PlateCarree(), zorder=5)

        # --- Grille & ticks ---
        ax.set_xticks(np.arange(np.floor(minx), np.ceil(maxx)+0.5, 0.5), crs=ccrs.PlateCarree())
        ax.set_yticks(np.arange(np.floor(miny), np.ceil(maxy)+0.5, 0.5), crs=ccrs.PlateCarree())
        ax.tick_params(labelsize=6)
        ax.gridlines(draw_labels=False, linewidth=0.2)

        # --- Barre de couleurs ---
        cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', shrink=0.75, pad=0.05, ticks=levels)
        cbar.set_label("Valeur", fontsize=6)
        cbar.ax.tick_params(labelsize=6)
        if len(str(levels[0]))>3 : cbar.set_ticks(levels[::2])

        # --- Sauvegarde ---
        print("carte_cpt_style created")
        plt.savefig("carte_cpt_style.png", dpi=300, bbox_inches='tight')
        plt.close()



    def create_map(self,df):
        import pandas as pd
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        from scipy.interpolate import griddata
        import numpy as np

        # Supposons que ton DataFrame s'appelle df
        # df = pd.read_csv('fichier.csv') si nécessaire

        # Création d'une grille régulière pour l'interpolation
        lon = df['lon']
        lat = df['lat']
        tmp = df['param']
        lon_grid = np.linspace(lon.min(), lon.max(), 100)
        lat_grid = np.linspace(lat.min(), lat.max(), 100)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

        # Interpolation des températures
        tmp_grid = griddata((lon, lat), tmp, (lon_mesh, lat_mesh), method='cubic')

        # Création de la carte
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
        cf = ax.contourf(lon_mesh, lat_mesh, tmp_grid, 60, cmap='plasma', transform=ccrs.PlateCarree())

        # Ajouts cartographiques
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.add_feature(cfeature.LAND, edgecolor='black', alpha=0.1)
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()])
        ax.set_title("Carte de Température (°C)")

        # Barres de couleur
        cbar = plt.colorbar(cf, ax=ax, orientation='vertical', shrink=0.7, label="Température (°C)")
        print("carte_temperature created")
        plt.savefig('carte_temperature.png', dpi=300, bbox_inches='tight')
        plt.close()
    def CPT_map(self,df):
        import pandas as pd
        import matplotlib.pyplot as plt
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        from scipy.interpolate import griddata
        import numpy as np

        # Supposons que ton DataFrame s'appelle df
        # Colonnes : lat, lon, TMP

        # Grille régulière pour interpolation
        lon = df['lon']
        lat = df['lat']
        tmp = df['param']
        lon_grid = np.linspace(lon.min(), lon.max(), 200)
        lat_grid = np.linspace(lat.min(), lat.max(), 200)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

        # Interpolation
        tmp_grid = griddata((lon, lat), tmp, (lon_mesh, lat_mesh), method='cubic')

        # Création de la carte type CPT
        fig, ax = plt.subplots(figsize=(11, 8.5), subplot_kw={'projection': ccrs.PlateCarree()})
        levels = np.linspace(np.nanmin(tmp_grid), np.nanmax(tmp_grid), 16)  # échelons lissés
        cmap = plt.cm.get_cmap("RdYlBu_r")  # palette CPT typique

        # Couleurs raster
        cf = ax.contourf(lon_mesh, lat_mesh, tmp_grid, levels=levels, cmap=cmap, extend='both')

        # Contours avec labels
        cs = ax.contour(lon_mesh, lat_mesh, tmp_grid, levels=levels, colors='black', linewidths=0.5)
        ax.clabel(cs, inline=True, fontsize=8, fmt="%.1f")

        # Cartographie de base
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.3, alpha=0.5)  # utile pour zooms
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()])
        ax.set_title("Température Moyenne (°C)", fontsize=14)

        # Barre de couleurs
        cbar = fig.colorbar(cf, ax=ax, orientation='horizontal', shrink=0.75, pad=0.05)
        cbar.set_label("Température (°C)")

        # Sauvegarde
        print("carte_temperature_cpt_style created")
        plt.savefig("carte_temperature_cpt_style.png", dpi=300, bbox_inches='tight')
        plt.close()
    def toMultiPolygone(self,shapes):
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

    def load_config(self,config_path=CONFIG_PATH):
        current_dir = os.path.dirname(__file__)  # répertoire où se trouve obswise.py
        config_path = os.path.join(current_dir, config_path)
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def get_db_connection(self,db_config):
        return psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password']
        )
    def get_previsions(self,sql):
        config = self.load_config()
        db_config = config.get("database")
        rows = {}
        conn = self.get_db_connection(db_config)
        cur = conn.cursor() #(cursor_factory=RealDictCursor)
        try:
            cur.execute(sql)
            rows = cur.fetchall()  # Liste de dictionnaires
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            cur.close()
            conn.close()
        return rows
    def fcst_wise(self,param,data):
        try :
            if param=='air_temperature_min':
                return round(float(data['TMP'].min()))
            elif param=='air_temperature_max':
                return round(float(data['TMP'].max()))
            elif param=='precipitation_amount':
                return round(float(data['PRATE'].sum()),1)
            elif param=='air_pressure_at_sea_level':
                return str(round(float(data['MSLET'].min()),1))+'/'+str(round(float(data['MSLET'].max()),1))
            # elif param=='wind_from_direction':
            #   return round(float(data['wind_direction']['mode_45']))
            elif param=='wind_speed':
                return str(int(math.floor(data['GUST'].min()*3.6 / 5) * 5))+'/'+str(int(math.ceil(data['GUST'].min()*3.6 / 5) * 5))
            elif param=='relative_humidity':
                return str(int(float(round(data['RH'].min()))))+'/'+str(int(float(round(data['RH'].max()))))
            elif param=="symbol_code":
                rr = float(data['PRATE'].sum())
                print(rr)
                symb='NP'
                match rr:
                    case s if s < 0.1:
                        symb="clearsky_day"
                    case s if 0.1 <= s < 1:
                        symb="cloudy"
                    case s if 1 <= s < 5:
                        symb="lightrain"
                    case s if 5 <= s < 15:
                        symb="rain"
                    case s if 15 <= s < 25:
                        symb="heavyrain"
                    case s if s >= 25:
                        symb="heavyrainandthunder"
                    case _:
                        symb="NP"
                vis = data['VIS'].min()
                if vis<5000 :
                    symb = 'fog'
                return symb
            else :
                return ""
        except :
            return ""