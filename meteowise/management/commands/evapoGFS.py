from django.utils import timezone
from datetime import datetime,timedelta
import os
# import yaml
import django
import pandas as pd


from pprint import pprint

from dateutil.parser import parse
from django.core.management.base import BaseCommand
from meteowise.utils import get_mean_sum_et0_gfs, get_archive_mean_sum_et0_gfs
from observation.models import ClimatDecades

class Command(BaseCommand):
	help = ('Get the evapotranspiration forecast from FGS model'
			'for all points in burkina and save it to the database.')
	def add_arguments(self, parser):
		parser.add_argument('--start', type=str, help="Date Debut YYYY-MM-DD")
		parser.add_argument('--end', type=str, help="Date Fin YYYY-MM-DD")

	def handle(self, *args, **options):
		start_str = options['start']
		if start_str:
			try:
				start_date = datetime.strptime(start_str, '%Y-%m-%d')
			except ValueError:
				self.stderr.write(self.style.ERROR("Date invalide. Format attendu : YYYY-MM-DD"))
				return
		else :
			start_date=None
		end_str = options['end']
		if end_str:
			try:
				end_date = datetime.strptime(end_str, '%Y-%m-%d')
			except ValueError:
				self.stderr.write(self.style.ERROR("Date invalide. Format attendu : YYYY-MM-DD"))
				return
		else :
			end_date = None
		if start_date and end_date :
			datas = get_archive_mean_sum_et0_gfs(start_str,end_str)
		else :
			datas = get_mean_sum_et0_gfs()

		now = datetime.now()
		print(now.strftime("[%Y-%m-%d %H:%M:%S]")+f" INFO Calcul de l evapotranspiration pour la periode {start_date} - {end_date}",end=' ')

		for df in datas :
			instances = [
			    ClimatDecades(
			        station=row.station,
			        lon=row.lon,
			        lat=row.lat,
			        decade=int(row.decade),
			        month=int(row.month),
			        year=int(row.year),
			        parameter=row.parameter,
			        value=row.value,
			        source=row.source
			    )
			    for row in df.itertuples(index=False)
			]
			# Enregistrer tous les objets en une seule requête
			ClimatDecades.objects.bulk_create(instances, ignore_conflicts=True)
