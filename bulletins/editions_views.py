from django.shortcuts import render, redirect, get_object_or_404
from forecast.models import *
from observation.models import *
from collections import defaultdict  
from django.views.generic import ListView, DetailView
from .models import *
from .forms import *
from datetime import datetime, date, timedelta
import locale

import os
from django.conf import settings
from django.http import HttpResponse

from collections import OrderedDict
from chartmet.utils import generate_observation_map, generate_forecast_map, generate_model_map

from pprint import pprint
import pprint as ppt
from .models import *
from forecast.utils import get_configured_elements_for_bulletin

from .utils import display_blocks #,display_blocks_old
import re
from django.contrib.auth.decorators import permission_required, login_required, permission_required

# Définir la locale en français (France)
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def select_bulletins(request):
	bulletins = BulletinTemplate.objects.filter(active=True)
	return render(request, 'editions/select_bulletins.html', {'bulletins': bulletins})

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def editBulletin(request, pk,date_bult):
	bulletin = get_object_or_404(BulletinTemplate, pk=pk)
	bulletin.established_date=datetime.strptime(date_bult,'%Y-%m-%d').date()
	context = display_blocks(bulletin,date_bult,modify=True)
	return render(request, "production/bulletin_detail.html",context)

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def save_observation(request,pk,date_bult):
	if request.method == 'POST':
		
		observation_value = request.POST.get('observation')
		obs_id=int(request.POST.get('obs_id'))
		param_id=int(request.POST.get('param'))
		zone_id=int(request.POST.get('zone'))
		heure=request.POST.get('heure')
		if obs_id==0: ## cas d'une nouvelle observation
			obs = Observation(
				date=datetime.strptime(date_bult,'%Y-%m-%d').date(),
				parametre=Variable.objects.get(id=param_id),
				station=Station.objects.get(id=zone_id),
				heure=heure,
				observation=observation_value
			)
			obs.save()
		else :
			try:
				obs = Observation.objects.get(id=obs_id)
				obs.observation = observation_value
				obs.save()
			except Observation.DoesNotExist:
				print("Observation inexistante")
				pass


	bulletin=BulletinTemplate.objects.get(pk=pk)
	bulletin.established_date=datetime.strptime(date_bult,'%Y-%m-%d').date()

	context = display_blocks(bulletin,date_bult,modify=True)
	return render(request, "production/bulletin_detail.html",context)

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def save_obsTable(request,pk,date_bult):
	if request.method == 'POST':
		data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

		for key, value in request.POST.items():
			if key.startswith('obs_'):
				match = re.match(r'obs_(\d+)_(\d+)_(\d+)_(\d+)', key)
				if match:
					zone_id, param_id, ech_id, obs_id = map(int, match.groups())
					if obs_id : data[zone_id][param_id][ech_id][obs_id] = value
					else : data[zone_id][param_id][ech_id][0] = value
	err=""
	for z in data :
		for p in data[z] :
			for e in data[z][p]:
				for ido,val in data[z][p][e].items() :
					if ido==0 :
						obs = Observation(
							date=datetime.strptime(date_bult,'%Y-%m-%d').date(),
							parametre=Variable.objects.get(id=p),
							station=Station.objects.get(id=z),
							heure=Echeance.objects.get(pk=e).echeance,
							observation=val
						)
						obs.save()
					else :
						try:
							obs = Observation.objects.get(id=ido)
							obs.observation = val
							obs.save()
						except Observation.DoesNotExist:
							err="Observation non enregistrée"
							pass


	bulletin=BulletinTemplate.objects.get(pk=pk)
	bulletin.established_date=datetime.strptime(date_bult,'%Y-%m-%d').date()

	context = display_blocks(bulletin,date_bult,modify=True)
	if err!="" : context['errors'].append(err)
	return render(request, "production/bulletin_detail.html",context)

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def save_fcstTable(request,pk,date_bult):
	if request.method == 'POST':
		data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

		for key, value in request.POST.items():
			if key.startswith('fcst_'):
				match = re.match(r'fcst_(\d+)_(\d+)_(\d+)_(\d+)', key)
				if match:
					zone_id, param_id, ech_id, fcst_id = map(int, match.groups())
					if fcst_id : data[zone_id][param_id][ech_id][fcst_id] = value
					else : data[zone_id][param_id][ech_id][0] = value
	err=""
	for z in data :
		for p in data[z] :
			for e in data[z][p]:
				for idf,val in data[z][p][e].items() :
					if idf==0 :
						fcst = Forecast(
							date=datetime.strptime(date_bult,'%Y-%m-%d').date(),
							parametre=Variable.objects.get(id=p),
							zone=Zone.objects.get(id=z),
							echeance=Echeance.objects.get(pk=e).echeance,
							prevision=val
						)
						fcst.save()
					else :
						try:
							fcst = Forecast.objects.get(id=idf)
							fcst.prevision = val
							fcst.save()
						except Forecast.DoesNotExist:
							err="Prévision non enregistrée"
							pass


	bulletin=BulletinTemplate.objects.get(pk=pk)
	bulletin.established_date=datetime.strptime(date_bult,'%Y-%m-%d').date()

	context = display_blocks(bulletin,date_bult,modify=True)
	if err!="" : context['errors'].append(err)
	return render(request, "production/bulletin_detail.html",context)

@permission_required('bulletins.edit_bulletin', raise_exception=True)
def save_forecast(request,pk,date_bult):
	if request.method == 'POST':
		
		forecast_value = request.POST.get('forecast')
		forecast_id=int(request.POST.get('forecast_id'))
		param_id=int(request.POST.get('param'))
		zone_id=int(request.POST.get('zone'))
		echeance=request.POST.get('echeance')
		if forecast_id==0: ## cas d'une nouvelle observation
			fcst = Forecast(
				date=datetime.strptime(date_bult,'%Y-%m-%d').date(),
				parametre=Variable.objects.get(id=param_id),
				zone=Zone.objects.get(id=zone_id),
				echeance=echeance,
				prevision=forecast_value
			)
			fcst.save()
		else :
			try:
				fcst = Forecast.objects.get(id=forecast_id)
				fcst.prevision = forecast_value
				fcst.save()
			except Forecast.DoesNotExist:
				print("Prévision inexistante")
				pass


	bulletin=BulletinTemplate.objects.get(pk=pk)
	bulletin.established_date=datetime.strptime(date_bult,'%Y-%m-%d').date()

	context = display_blocks(bulletin,date_bult,modify=True)
	return render(request, "production/bulletin_detail.html",context)