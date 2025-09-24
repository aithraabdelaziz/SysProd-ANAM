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
	def add_arguments(self, parser):
		parser.add_argument('--date', type=str, help="Date du run YYYY-MM-DD")
		parser.add_argument('--from', type=str, help="Echeance Début")
		parser.add_argument('--to', type=str, help="Echeance Fin")

	def handle(self, *args, **options):
		nb_jour = 115
		date_retention = timezone.now() - timedelta(days=nb_jour)
		prevsions_a_supprimer = Forecast.objects.filter(date__lt=date_retention)
		prevsions_a_supprimer.delete()
		# print("prévisions antérieur à "+date_retention.strftime("%d-%m-%Y")+" supprimées---------------")

		cities = Zone.objects.filter(category='ville')
		latlon = {c:(c.geom.y,c.geom.x) for c in cities}
		results = {}

		date_str = options['date']
		if date_str:
			try:
				date_run = datetime.strptime(date_str, '%Y-%m-%d')
			except ValueError:
				self.stderr.write(self.style.ERROR("Date invalide. Format attendu : YYYY-MM-DD"))
				return
		else:
			date_run=timezone.now().strftime("%Y-%m-%d")

		fromEch = options['from']
		if fromEch:
			try:
				fromEch = int(fromEch)
			except ValueError:
				self.stderr.write(self.style.ERROR("Echeance doit être un entier entre 0 et 340"))
				return
		else:
			fromEch=12

		toEch = options['to']
		if toEch:
			try:
				toEch = int(toEch)
			except ValueError:
				self.stderr.write(self.style.ERROR("Echeance doit être un entier entre 0 et 340"))
				return
		else:
			toEch=36

		try :
			ech = Echeance.objects.get(start=fromEch,end=toEch)
		except Exception:
			self.stderr.write(self.style.ERROR(f"Echéance {fromEch}-{toEch} non configurée"))
			return
		now = datetime.now()
		print(now.strftime("[%Y-%m-%d %H:%M:%S]")+f" INFO Calcul de la prévision de la periode {date_run} de {fromEch} à {toEch}")
		
		heure_run = "00"
		req1=f"""
				SELECT DISTINCT lat, long
				FROM gfs_model.weather_data
				WHERE ech BETWEEN 12 AND 36 AND date='{date_run}' AND cycle='{heure_run}'
			"""
		coords = self.get_previsions(req1)
		if len(coords)==0:
			self.stderr.write(self.style.ERROR(f"Prévision pour  date='{date_run}' et cycle='{heure_run}' indisponible"))
			return
		for city, (lat_c, lon_c) in latlon.items():
			# Récupérer les données avec ech entre 12 et 36
			
			# Trouver la ligne la plus proche géographiquement
			# closest_row = min(
			#	 rows,
			#	 key=lambda row: math.sqrt((row[1] - lat_c) ** 2 + (row[2] - lon_c) ** 2)
			# )
			closest_lat, closest_lon = min(
				coords,
				key=lambda row: math.sqrt((row[0] - lat_c)**2 + (row[1] - lon_c)**2)
			)
			
			req2 = """
				SELECT ech,lat,long,data
				FROM gfs_model.weather_data
				WHERE lat = %s AND long = %s AND ech BETWEEN %d AND %d AND date='%s' AND cycle='%s' order by ech
			""" % (closest_lat, closest_lon,fromEch,toEch,date_run,heure_run)
			rows = self.get_previsions(req2)
			results[city] = pd.DataFrame([
				{'ech': ech,'lat': lat,'lon': lon, **vars_dict} for ech,lat,lon, vars_dict in rows
			])

		for c,data in results.items():
			#print(f'{date_run}---------{c}===========================')
			for nmv in VARIABLES:
				vv=Variable.objects.get(shortName=nmv['sn'])
				prev_desc = self.fcst_wise(nmv['sn'],data)
				if prev_desc!="":
					# print('*******',end='')
					# print(nmv['sn'], end=" : ")
					# print(prev_desc, end="; ")
					with transaction.atomic():
						prev, created = Forecast.create_or_update(
							zone=c,
							date=date_run,
							echeance=ech.echeance,
							parametre=vv,
							prevision=prev_desc
						)
						prev.save()
		quit() #return True


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
				return round(float(data['TMIN'].min()))
			elif param=='air_temperature_max':
				return round(float(data['TMAX'].max()))
			elif param=='precipitation_amount':
				return round(float(data['APCP'].sum()),1)
			elif param=='air_pressure_at_sea_level':
				return str(round(float(data['MSLET'].min()),1))+'/'+str(round(float(data['MSLET'].max()),1))
			# elif param=='wind_from_direction':
			# 	return round(float(data['wind_direction']['mode_45']))
			elif param=='wind_speed':
				return str(int(math.floor(data['GUST'].min()*3.6 / 5) * 5))+'/'+str(int(math.ceil(data['GUST'].min()*3.6 / 5) * 5))
			elif param=='relative_humidity':
				return str(int(float(round(data['RH'].min()))))+'/'+str(int(float(round(data['RH'].max()))))
			elif param=="symbol_code":
				
				symb='NP'
				cld = float(data['TCDC'].mean())
				# print(f'cld---------{cld}')
				match cld:
					case s if 0 <= s <  10:
						symb="clearsky_day"
					case s if 10 <= s < 40:
						symb="fair_day"
					case s if 40 <= s < 80:
						symb="partlycloudy_day"
					case s if s >= 80:
						symb="cloudy"
					case _:
						symb="NP"
				vis = data['VIS'].min()
				if vis<5000 :
					symb = 'fog'
				rr = float(data['APCP'].sum())
				# print(f'rr---------{rr}')
				if rr >=1 :
					match rr:
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


