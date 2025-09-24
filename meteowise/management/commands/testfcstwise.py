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

class Command(BaseCommand):
	help = ('Get the weather forecast from FGS model'
			'for all cities in the database and save it to the database.')

	def handle(self, *args, **options):
		nb_jour = 5
		date_retention = timezone.now() - timedelta(days=nb_jour)
		prevsions_a_supprimer = Forecast.objects.filter(date__lt=date_retention)
		prevsions_a_supprimer.delete()
		print("prévisions antérieur à "+date_retention.strftime("%d-%m-%Y")+" supprimées---------------")
		req = """WITH parsed_data AS (
			  SELECT
				wigos_station_identifier,
				parameter,
				value,
				-- extraction du timestamp réel
				CASE
				  WHEN phenomenon_time LIKE '%/%'
				  THEN CAST(SPLIT_PART(phenomenon_time, '/', 2) AS timestamp)
				  ELSE CAST(phenomenon_time AS timestamp)
				END AS phenomenon_timestamp
			  FROM wis2.observations
			)
			SELECT
			  wigos_station_identifier,
			  parameter,
			  AVG(value) AS avg,
			  MIN(value) AS min,
			  MAX(value) AS max,
			  SUM(value) AS sum,
			  MODE() WITHIN GROUP (ORDER BY ROUND(value / 10.0) * 10) AS mode_10,
			  MODE() WITHIN GROUP (ORDER BY ROUND(value / 45.0) * 45) AS mode_45,
			  MODE() WITHIN GROUP (ORDER BY ROUND(value)) AS mode
			FROM parsed_data
			WHERE phenomenon_timestamp >= date_trunc('day', now()) - interval '1 day' + interval '9 hour'
			  AND phenomenon_timestamp <  date_trunc('day', now()) + interval '9 hour'
			GROUP BY wigos_station_identifier, parameter
			ORDER BY wigos_station_identifier, parameter;
			"""
		raw_data_obs = self.get_observation(req)
		data_obs= defaultdict(lambda: defaultdict(list))
		for d in raw_data_obs:
			data_obs[d['wigos_station_identifier']][d['parameter']]={'max':d['max'],'min':d['min'],'avg':d['avg'],'sum':d['sum'],'mode':d['mode'],'mode_10':d['mode_10'],'mode_45':d['mode_45']}

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

		date_ini = datetime.now()
		ech = Echeance.objects.get(echeance="9 last 24h")
		for wigos_id,data in data_obs.items():
			print(f'---------{wigos_id}')
			stat = Station.objects.get(wigos_id=wigos_id)
			for nmv in VARIABLES:
				vv=Variable.objects.get(shortName=nmv['sn'])
				obs_desc = self.obs_wise(nmv['sn'],data)
				if obs_desc!="":
					print('*******',end='')
					print(nmv['sn'], end=" : ")
					print(obs_desc, end="; ")
					with transaction.atomic():
						obs, created = Observation.create_or_update(
							station=stat,
							date=date_ini.strftime('%Y-%m-%d'),
							heure=ech.echeance,
							parametre=vv,
							observation=obs_desc
						)
						obs.save()


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
	def get_observation(self,sql):
		config = self.load_config()
		db_config = config.get("database")
		rows = {}
		conn = self.get_db_connection(db_config)
		cur = conn.cursor(cursor_factory=RealDictCursor)
		try:
			cur.execute(sql)
			rows = cur.fetchall()  # Liste de dictionnaires
		except Exception as e:
			print(f"Error occurred: {e}")
		finally:
			cur.close()
			conn.close()
		return rows
	def obs_wise(self,param,data):
		try :
			if param=='air_temperature_min':
				return round(float(data['air_temperature']['min']))
			elif param=='air_temperature_max':
				return round(float(data['air_temperature']['max']))
			elif param=='precipitation_amount':
				return round(float(data['total_precipitation_or_total_water_equivalent']['sum']),1)
			elif param=='air_pressure_at_sea_level':
				return str(round(float(data['non_coordinate_pressure']['min']),1))+'/'+str(round(float(data['non_coordinate_pressure']['max']),1))
			elif param=='wind_from_direction':
				return round(float(data['wind_direction']['mode_45']))
			elif param=='wind_speed':
				return str(int(math.floor(data['wind_speed']['min']*3.6 / 5) * 5))+'/'+str(int(math.ceil(data['wind_speed']['max']*3.6 / 5) * 5))
			elif param=='relative_humidity':
				return str(int(float(round(data['relative_humidity']['min']))))+'/'+str(int(float(round(data['relative_humidity']['max']))))
			elif param=="symbol_code":
				rr = float(data['total_precipitation_or_total_water_equivalent']['sum'])
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
				return symb
			else :
				return ""
		except :
			return ""


