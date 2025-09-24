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


from forecast.models import Variable
from observation.models import Observation, Station
from django.db import transaction




import yaml

import psycopg2
from psycopg2.extras import RealDictCursor
import math


main_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(main_folder_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "climforge.settings.dev")
django.setup()
from forecast.models import Variable
from observation.models import Station, Observation
from bulletins.models import  Echeance
from django.db import transaction
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from collections import defaultdict

CONFIG_PATH = 'config.yaml'

class Command(BaseCommand):
	help = ('Get the weather observation from WIS2NODE'
			'for all cities in the database and save it to the database.')
	
	def add_arguments(self, parser):
		parser.add_argument('--date', type=str, help="Date d'observation au format YYYY-MM-DD")
		parser.add_argument('--hour', type=str, help="Heure d'observation un entier de 0 à 23")

	def handle(self, *args, **options):
		date_str = options['date']
		hour_str = options['hour']
		if date_str:
			try:
				date_ref = datetime.strptime(date_str, '%Y-%m-%d')
			except ValueError:
				self.stderr.write(self.style.ERROR("Date invalide. Format attendu : YYYY-MM-DD"))
				return
		else:
			self.stderr.write(self.style.ERROR("Date invalide. Format attendu : YYYY-MM-DD"))
			return

		if hour_str:
			try:
				hour = int(hour_str)
			except ValueError:
				self.stderr.write(self.style.ERROR("Heure invalide. un entier est attendu"))
				return
			if hour<0 or hour >23 :
				self.stderr.write(self.style.ERROR("Heure invalide. doit etre entre 0 et 23"))
				return
		else:
			self.stderr.write(self.style.ERROR("Heure invalide. un entier est attendu"))
			return
		nb_jour = 115
		date_retention = timezone.now() - timedelta(days=nb_jour)
		observations_a_supprimer = Observation.objects.filter(date__lt=date_retention)
		observations_a_supprimer.delete()
		# print("Observations antérieur à "+date_retention.strftime("%d-%m-%Y")+" supprimées---------------")
		now = datetime.now()
		print(now.strftime("[%Y-%m-%d %H:%M:%S]")+" INFO Insertion de l'observation du "+date_str+ ' à ' + hour_str+'H')
		
		date_sql = date_ref.strftime('%Y-%m-%d')
		req = """ WITH parsed_data AS (
			  SELECT
				wigos_station_identifier,
				parameter,
				value,
				report_time
			  FROM wis2.observations
			)
			SELECT
			  wigos_station_identifier,
			  parameter,
			  value
			FROM parsed_data
			WHERE report_time = TIMESTAMP '%s %02d:00:00'
			ORDER BY wigos_station_identifier, parameter; 
			""" % (date_sql,hour)

		raw_data_obs = self.get_observation(req)
		data_obs= defaultdict(lambda: defaultdict(list))
		for d in raw_data_obs:
			data_obs[d['wigos_station_identifier']][d['parameter']]=d['value']

		VARIABLES = [
			{"name": "Minimum Air Temperature", "sn": "air_temperature_min", "unit": "°C",'cat':'value'},
			{"name": "Maximum Air Temperature", "sn": "air_temperature_max", "unit": "°C",'cat':'value'},
			{"name": "Pluie", "sn": "precipitation_amount", "unit": "mm",'cat':'value'},
			{'name':'Pression','sn':'air_pressure_at_sea_level','unit':'hPa','cat':'value'},
			{'name':'Direction','sn':'wind_from_direction','unit':'°','cat':'value'},
			{'name':'Force','sn':'wind_speed','unit':'km/h','cat':'value'},
			{"name": "Conditions", "sn": "symbol_code", "unit": "",'cat':'class'},
			{"name": "Humidité", "sn": "relative_humidity", "unit": "%",'cat':'value'},
			{"name": "Temps sensible", "sn": "symbol_code", "unit": "",'cat':'class'},
			{"name": "Temperature", "sn": "air_temperature", "unit": "°C",'cat':'value'}


		]

		date_ini = datetime.now()
		ech = Echeance.objects.get(start=hour,end=hour)
		if len(data_obs)==0 :
			print(f'---- observation indisponible pour {date_str} à {hour_str}')
		for wigos_id,data in data_obs.items():
			# print(f'---------{wigos_id}--{date_str} à {hour_str}')
			stat = Station.objects.get(wigos_id=wigos_id)
			for nmv in VARIABLES:
				vv=Variable.objects.get(shortName=nmv['sn'])
				obs_desc = self.obs_hour(nmv['sn'],data)
				if obs_desc!="":
					# print('*******',end='')
					# print(nmv['sn'], end=" : ")
					# print(obs_desc, end="; ")
					with transaction.atomic():
						obs, created = Observation.create_or_update(
							station=stat,
							date=date_ref.strftime('%Y-%m-%d'),
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
	def obs_hour(self,param,data):
		try :
			if param=='air_temperature':
				return round(float(data['air_temperature']))
			elif param=='precipitation_amount':
				return round(float(data['total_precipitation_or_total_water_equivalent']),1)
			elif param=='air_pressure_at_sea_level':
				return str(float(data['non_coordinate_pressure']))
			elif param=='wind_from_direction':
				return round(float(data['wind_direction']))
			elif param=='wind_speed':
				return str(int(math.floor(data['wind_speed']*3.6 / 5) * 5))
			elif param=='relative_humidity':
				return str(int(float(round(data['relative_humidity']))))
			elif param=="symbol_code":
				rr = float(data['total_precipitation_or_total_water_equivalent'])
				# print(rr)
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