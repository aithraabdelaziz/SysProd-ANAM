from datetime import datetime,timedelta, timezone
import os
import sys
# import yaml
import django
import pandas as pd

import requests
from concurrent.futures import ThreadPoolExecutor
import time
import json

from pprint import pprint
from scipy.stats import mode

import pandas as pd
import numpy as np
from scipy.stats import mode
# Configuration
USER_AGENT = "climWeb/1.0 abdelaziz.aithra@gmail.com"  # Obligatoire
BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
# Liste des colonnes à extraire
COLUMNS = [
    'air_pressure_at_sea_level',
    'air_temperature',
    'cloud_area_fraction',
    'cloud_area_fraction_high',
    'cloud_area_fraction_low',
    'cloud_area_fraction_medium',
    'dew_point_temperature',
    'relative_humidity',
    'wind_from_direction',
    'wind_speed'
]

COLUMNS_6HOURS = [
    "air_temperature_min",
    "air_temperature_max",
    "precipitation_amount",
    "symbol_code"
]

VARIABLES =[
    {'name':'Pression','sn':'air_pressure_at_sea_level','unit':'hPa','cat':'value'},
    {'name':'Temperature','sn':'air_temperature','unit':'°C','cat':'value'},
    {'name':'Nuages','sn':'cloud_area_fraction','unit':'%','cat':'value'},
    {'name':'Nuages hauts','sn':'cloud_area_fraction_high','unit':'%','cat':'value'},
    {'name':'Nuages bas','sn':'cloud_area_fraction_low','unit':'%','cat':'value'},
    {'name':'Nuages moyens','sn':'cloud_area_fraction_medium','unit':'%','cat':'value'},
    {'name':'Point rosée','sn':'dew_point_temperature','unit':'C','cat':'value'},
    {'name':'Humidité','sn':'relative_humidity','unit':'%','cat':'value'},
    {'name':'Direction','sn':'wind_from_direction','unit':'°','cat':'value'},
    {'name':'Force','sn':'wind_speed','unit':'km/h','cat':'value'},

]

DEFAULT_NEXT_HOURS_DATA_PARAMETERS = [
    {"name": "Minimum Air Temperature", "sn": "air_temperature_min", "unit": "°C",'cat':'value'},
    {"name": "Maximum Air Temperature", "sn": "air_temperature_max", "unit": "°C",'cat':'value'},
    {"name": "Precipitation Amount", "sn": "precipitation_amount", "unit": "mm",'cat':'value'},
    {"name": "Conditions", "sn": "symbol_code", "unit": "",'cat':'class'},

]
VARIABLES +=DEFAULT_NEXT_HOURS_DATA_PARAMETERS
import numpy as np
from dateutil.parser import parse
from django.core.management.base import BaseCommand
# main_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
# sys.path.append(main_folder_path)
# from functions import parameter_in_zone, get_stats_in_zone, get_txn_from_csv, idx_in_zone, convert_to_list
# from Algorithmes import TemperatureAlgorithme as algo
# sys.path.remove(main_folder_path)

main_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(main_folder_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "climforge.settings.dev")
django.setup()
from forecast.models import Variable, Forecast, Zone
from django.db import transaction


class Command(BaseCommand):
    help = ('Get the weather forecast from API CEP Norvege'
            'for all cities in the database and save it to the database.')

    def handle(self, *args, **options):


        nb_jour = 5
        date_retention = datetime.now(timezone.utc) - timedelta(days=nb_jour)
        previsions_a_supprimer = Forecast.objects.filter(date__lt=date_retention)
        previsions_a_supprimer.delete()
        print("prévisions antérieur à "+date_retention.strftime("%d-%m-%Y")+" supprimées---------------")
        zones = list(Zone.objects.filter(category='ville').order_by('name'))
        locations = zones #[z.geom.coords for z in zones]
        # locations=locations[:1]
        print(f"Nombre de points à traiter: {len(locations)}")
        
        results = []
        max_workers = 2  # Respect du rate limiting
        # self.create_variables(VARIABLES)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_loc = {executor.submit(self.get_weather, z.geom.coords[1], z.geom.coords[0]): z 
                            for z in locations}  # Limité à 20 points pour l'exemple
            
            j=1
            for future in future_to_loc:
                zz = future_to_loc[future]
                print(zz)
                json_data = future.result()
                # pprint(json_data)
                
                if json_data:
                
                    weather_data = self.parse_6hours_weather_json(json_data)
                #     weather_data = calculate_12h_stats(weather_data)
                #     pprint(weather_data)
                    forecasts = self.save_forecast_6hours(weather_data,zz)   
                    print(f'{j} - inserted')
                    j+=1       
                time.sleep(0.6)  # Respect du rate limiting (1 req/sec)
    def create_variables(self,varis):
        for var in varis :
            with transaction.atomic():
                vv, created = Variable.create_or_update(
                        name=var['name'],
                        shortName=var['sn'],
                        active=True,
                        unit=var['unit'],
                        category=var['cat']
                    )
                vv.save()

    def get_weather(self,lat, lon):
        headers = {"User-Agent": USER_AGENT}
        params = {"lat": lat, "lon": lon}
        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erreur pour ({lat}, {lon}): {str(e)}")
            return None


    # 3. Analyse du XML et extraction des données
    def parse_weather_json(self,data):

        # Création du DataFrame optimisé
        df = pd.DataFrame([
            {**{'time': entry['time']}, 
             **{col: entry['data']['instant']['details'].get(col) for col in COLUMNS}}
            for entry in data['properties']['timeseries']
        ])

        # Conversion des types et optimisation
        df['time'] = pd.to_datetime(df['time'])
        df = df.astype({
            'air_pressure_at_sea_level': 'float32',
            'air_temperature': 'float32',
            'dew_point_temperature': 'float32',
            'relative_humidity': 'float32',
            'wind_from_direction': 'float32',
            'wind_speed': 'float32'
        })
        return df

    def parse_6hours_weather_json(self,data,max_ech=72):

        # Création du DataFrame optimisé
        df = pd.DataFrame([
            {**{'time': entry['time']}, 
             **{col: entry['data']['next_6_hours']['details'].get(col) for col in COLUMNS_6HOURS[:-1]}}
            for entry in data['properties']['timeseries'] if 'next_6_hours' in entry['data']
        ])
        # Conversion des types et optimisation
        df['time'] = pd.to_datetime(df['time'])
        df = df.astype({
            'air_temperature_min': 'float32',
            'air_temperature_max': 'float32',
            'precipitation_amount': 'float32'
        })

        df2 = pd.DataFrame([
            {**{'time': entry['time']}, 
             **{'symbol_code': entry['data']['next_6_hours']['summary'].get('symbol_code') }}
            for entry in data['properties']['timeseries'] if 'next_6_hours' in entry['data']
        ])

        # Conversion des types et optimisation
        df2['time'] = pd.to_datetime(df['time'])
        df2 = df2.astype({
            'symbol_code': 'string'
        })
        merged_df = pd.merge(df, df2, on='time', how='outer')  # 'inner', 'outer', 'left', 'right'

        merged_df['time'] = pd.to_datetime(merged_df['time'], utc=True)

        # Date de run = aujourd'hui à 00:00 UTC
        run_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        # Ajouter la colonne 'run'
        merged_df['run'] = run_date
        # Calcul de l'échéance en heures
        merged_df['echeance'] = (merged_df['time'] - run_date).dt.total_seconds() // 3600
        merged_df = merged_df[merged_df['echeance'] % 6 == 0] # seule les multiple de 6 son extraites
        merged_df['echeance'] = merged_df['echeance'].astype(int)+6 ### on a ajouté 6 car la prévision est pour les 6 heures prochaines
        merged_df=merged_df[merged_df['echeance']<=max_ech]
        return merged_df

    def calculate_12h_stats(self,df):
        # Conversion en datetime et tri
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Création des groupes de 12h (00:00-12:00 et 12:00-00:00)
        df['period'] = df['time'].dt.floor('12h')

        df['wind_from_direction'] = (df['wind_from_direction'] / 10).round() * 10
        df['wind_speed'] = (df['wind_speed']*3.6 / 5).round() * 5
        df['cloud_area_fraction'] = (df['cloud_area_fraction'] / 10).round() * 10
        df['cloud_area_fraction_high'] = (df['cloud_area_fraction_high'] / 10).round() * 10
        df['cloud_area_fraction_medium'] = (df['cloud_area_fraction_medium'] / 10).round() * 10
        df['cloud_area_fraction_low'] = (df['cloud_area_fraction_low'] / 10).round() * 10
        df['air_pressure_at_sea_level'] = df['air_pressure_at_sea_level'].round(1)
        df['air_temperature'] = df['air_temperature'].round()
        df['dew_point_temperature'] = df['dew_point_temperature'].round()
        
        # Fonction pour calculer le mode
        def get_mode(series):
            try:
                return mode(series.dropna(), keepdims=True)[0][0]
            except:
                return np.nan
        
        # Calcul des statistiques
        result = df.groupby('period').agg({
            'air_pressure_at_sea_level': ['min', 'max'],
            'air_temperature': ['min', 'max'],
            'cloud_area_fraction': get_mode,
            'cloud_area_fraction_high': get_mode,
            'cloud_area_fraction_low': get_mode,
            'cloud_area_fraction_medium': get_mode,
            'dew_point_temperature': ['min', 'max'],
            'relative_humidity': ['min', 'max'],
            'wind_from_direction': get_mode,
            'wind_speed': ['min', 'max']
        })
        
        # Renommage des colonnes
        result.columns = [
            'air_pressure_at_sea_level_min', 'air_pressure_at_sea_level_max',
            'air_temperature_min', 'air_temperature_max',
            'cloud_area_fraction_mode',
            'cloud_area_fraction_high_mode',
            'cloud_area_fraction_low_mode',
            'cloud_area_fraction_medium_mode',
            'dew_point_temperature_min', 'dew_point_temperature_max',
            'relative_humidity_min', 'relative_humidity_max',
            'wind_from_direction_mode',
            'wind_speed_min', 'wind_speed_max'
        ]
        
        # Formatage de la période
        # result['date'] = result['period_start'].dt.strftime('%Y-%m-%d') 
        # result['period'] = pd.to_datetime(result['period'])
        # Réorganisation des colonnes
        # cols = ['period'] + [col for col in result.columns if col not in ['period', 'period_start', 'period_end']]
        # result = result[cols].reset_index(drop=True)
        
        return result

    def save_forecast_12hours(self,df,zone):
        date_ini = df.index.min() - timedelta(hours=12)
        i=1
        for index, row in df.iterrows():
            # date_ini = index - timedelta(hours=12)
            ech = i*12#date_ini.strftime('%HhOO') + ' - ' + index.strftime('%Hh00')
            print(ech)
            i=i+1
            for nmv in COLUMNS:
                vv=Variable.objects.get(shortName=nmv)
                if nmv in ['air_pressure_at_sea_level','air_temperature','dew_point_temperature','relative_humidity','wind_speed']:
                    if row[f'{nmv}_min'].round()<row[f'{nmv}_max'].round() : previ_finale = str(row[f'{nmv}_min'].round()) + '/' + str(row[f'{nmv}_max'].round())
                    else :previ_finale = str(row[f'{nmv}_min'].round())

                elif nmv in ['wind_from_direction','cloud_area_fraction','cloud_area_fraction_high','cloud_area_fraction_low','cloud_area_fraction_medium'] :
                    previ_finale = str(row[f'{nmv}_mode'].round())

                with transaction.atomic():
                    previ, created = Forecast.create_or_update(
                        zone=zone,
                        date=date_ini.strftime('%Y-%m-%d'),
                        echeance=ech,
                        parametre=vv,
                        prevision=previ_finale
                    )
                    previ.save()

                # print(f"Période : {row['period']}")
                # print(f"Pression min : {row['air_pressure_min']} hPa")
                # print(f"Pression max : {row['air_pressure_max']} hPa")
                # print(f"Température min : {row['air_temp_min']}°C")
                # print(f"Température max : {row['air_temp_max']}°C")
                # print(f"Direction du vent dominante : {row['wind_direction_mode']}°")
                # print(f"Vitesse vent min : {row['wind_speed_min']} m/s")
                # print(f"Vitesse vent max : {row['wind_speed_max']} m/s")
                # print("-----------------------------")
    def save_forecast_6hours(self,df,zone,ech_max=72):
        for index, row in df.iterrows():
            for nmv in COLUMNS_6HOURS:
                vv=Variable.objects.get(shortName=nmv)
                if nmv in ['air_temperature_min','air_temperature_max','precipitation_amount']:
                    previ_finale = str(round(row[nmv]))

                elif nmv in ['symbol_code'] :
                    previ_finale = str(row[nmv])
                ech = row['echeance']
                # print(f'{zone.name} : {ech}-{previ_finale}')
                with transaction.atomic():
                    previ, created = Forecast.create_or_update(
                        zone=zone,
                        date=row['run'].strftime('%Y-%m-%d'),
                        echeance=ech,
                        parametre=vv,
                        prevision=previ_finale
                    )
                    previ.save()
