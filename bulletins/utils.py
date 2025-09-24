
from collections import defaultdict
from django.apps import apps
from datetime import datetime, date, timedelta
import locale
import os
from collections import OrderedDict
from chartmet.utils import generate_observation_map, generate_forecast_map, generate_model_map, generate_points_map, generate_Spatial_points_map, generate_Decadaire_map
from meteowise.symbols_select import render_weather_icon_select

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
from forecast.models import Variable,Zone
from observation.models import Observation, Station
from bulletins.models import Echeance
from django.conf import settings

from pprint import pprint

def get_current_decade_code(date_now=None):
    if date_now is not None : 
        if isinstance(date_now,datetime) : today = date_now.date()
        elif isinstance(date_now,date) : today = date_now
        else : today = date.today()
    else : today = date.today()
    day = today.day
    month = today.month
    year = today.year

    # Calcul de la décade (01 = 1-10, 02 = 11-20, 03 = 21-fin)
    if day <= 10:
        decade = "01"
    elif day <= 20:
        decade = "02"
    else:
        decade = "03"

    # Format final : JJMMYYYY
    code = f"{decade}{month:02d}{year}"
    return code
def format_periode(display_periode,ech,date_bult):
    date_bult = datetime.combine(date_bult, datetime.min.time())
    if not display_periode :
        return ""
    emax = max([ h.start for h in ech]+[ h.end for h in ech])
    emin = min([ h.start for h in ech]+[ h.end for h in ech])
    d1 = date_bult + timedelta(hours=emin)
    d2 = date_bult + timedelta(hours=emax)
    periode = ""
    if (d2-d1) >= timedelta(days=2):
        if d1.strftime("%B") == d2.strftime("%B") :
            if d2.strftime("%H")=='00' : d2 = d2 - timedelta(hours=1)
            periode = d1.strftime("%A %d") + " au "+d2.strftime("%A %d %B %Y")
        else :
            periode = d1.strftime("%A %d %B") + " au "+d2.strftime("%A %d %B %Y")
    else :
        if d1.strftime("%B") == d2.strftime("%B") :
            periode = "du "+d1.strftime("%A %d à %Hh") + " au "+d2.strftime("%A %d %B %Y à %Hh")
        else :
            periode = "du "+d1.strftime("%A %d %B à %Hh") + " au "+d2.strftime("%A %d %B %Y à %Hh")
    return periode

def generate_echeances_dict(date_bult, echeances):
   
    # Dictionnaire pour stocker les résultats
    date_echeances_dict = {}

    # Variable pour suivre le jour d'ajout
    current_date = date_bult

    # Boucle pour remplir le dictionnaire
    for ech in echeances :
        # if isinstance(ech.echeance,int) : 
        #     current_date = date_bult + timedelta(hours=(ech.echeance-1))
        # if current_date not in date_echeances_dict:
        #     date_echeances_dict[current_date]={}
        try :
            echint = int(ech.echeance)
            current_date = date_bult + timedelta(hours=(echint-1))
        except :
            pass
        if current_date not in date_echeances_dict:
            date_echeances_dict[current_date]={}
        date_echeances_dict[current_date][ech.echeance]=ech.name

    return date_echeances_dict
def get_style(block):
    all_styles = {}

    if not isinstance(block, dict):
        return all_styles

    # -------- STYLE TITRE --------
    s = block.get('style_title')
    if s:
        style_parts = [
            f"color: {s.get('title_color', '#000000')};",
            f"font-size: {s.get('title_size', 14)}px;",
        ]
        if s.get('title_bold'):
            style_parts.append("font-weight: bold;")
        if s.get('title_underline'):
            style_parts.append("text-decoration: underline;")
        all_styles['title'] = " ".join(style_parts)

    # -------- STYLE TABLE --------
    s = block.get('style_table')
    if s:
        style_parts = [
            f"color: {s.get('table_color', '#000000')};",
            f"font-size: {s.get('table_size', 12)}px;",
        ]
        if s.get('table_bold'):
            style_parts.append("font-weight: bold;")
        all_styles['table'] = " ".join(style_parts)

    # -------- STYLE TEXTE --------
    s = block.get('style_text')
    if s:
        style_parts = [
            f"color: {s.get('text_color', '#000000')};",
            f"font-size: {s.get('text_size', 14)}px;",
            f"order: {s.get('text_align', '0')};",
            f"width: {s.get('width_percentage', 100)}%;",
            f"background-color: {s.get('bg_color', '#FFFFFF')};",
        ]
        if s.get('text_bold'):
            style_parts.append("font-weight: bold;")
        if s.get('text_italic'):
            style_parts.append("font-style: italic;")
        if s.get('text_underline'):
            style_parts.append("text-decoration: underline;")
        all_styles['text'] = " ".join(style_parts)

    # -------- STYLE IMAGE --------
    s = block.get('style_img')
    if s:
        style_parts = [
            f"width: {s.get('image_width', 100)}%;",
            f"display: block;",
        ]
        
        style_parts.append(f"order: {s.get('image_align', '0')};")
        
        all_styles['image'] = " ".join(style_parts)

    return all_styles

def display_blocks(bulletin,date_bult,modify=False,initialize=False):
    context={}
    error_msg=[]
    if isinstance(date_bult,str):
        date_obj=datetime.strptime(date_bult, "%Y-%m-%d")
        date_bult = date_obj.date()
    block_contexts = {}

    import time
    figNum=1
    for b in bulletin.content:
        start_time = time.time()
        style = get_style(b.value)
        if b.block_type == 'ObsTableBlock':
            stations = b.value['stations']
            heures_obj = b.value['heures']
            display_periode = b.value['periode']
            periode = format_periode(display_periode,heures_obj,date_bult)
            heures = [ech.echeance for ech in heures_obj]
            obs_parameters = b.value['parametres']
            obs_data = b.block.get_obs_data(date_bult,obs_parameters,stations,heures)
            
            if len(obs_data) == 0 :
                error_msg.append('Observation indisponible')
                continue

            heures_obj = sorted(heures_obj, key=lambda hh: hh.end)
            jours = generate_echeances_dict(date_bult, heures_obj)
            stations = sorted(stations, key=lambda st: st.name)
            obs_parameters = sorted(obs_parameters, key=lambda pp: pp.name)
                        
            # z = Station.objects.filter(name=zone).first()
            for z in obs_data:
                for paramid in obs_data[z]:
                    pp = obs_data[z][paramid]
                    paramSN = Variable.objects.get(pk=paramid)
                    if paramSN.shortName=='symbol_code': # traitement spécial de symboles
                        if modify :
                            pp = {ech : (p[0],render_weather_icon_select(name=f"obs_{z}_{paramid}_{ech}_{p[0]}",selected=p[1])) for ech,p in pp.items()}
                        else :
                            pp = {ech : (p[0],'<img class="weather_icon" src="'+os.path.join('/media','weathericons',f'{p[1]}.png')+'"/>') for ech,p in pp.items()}
                        obs_data[z][paramid] = pp
               
            block_contexts[b.id] = {
                'obst_obs_data': obs_data,
                'obst_sorted_heures': [{'id':hh.id,'name':hh.name} for hh in heures_obj],
                'obst_stations': [{'id':st.id,'name':st.name} for st in stations],
                'obst_jours_obs': jours,
                'obst_parameters':[{'id':pp.id,'name':pp.name} for pp in obs_parameters],
                'obst_periode': periode
            }
        elif b.block_type=='FcstTableBlock':
            villes = b.value['zones']
            echeances_obj = b.value['echeances']
            display_periode = b.value['periode']
            periode = format_periode(display_periode,echeances_obj,date_bult)
            echeances = [ech.echeance for ech in echeances_obj]
            fcst_parameters = b.value['parametres']
            fcst_data = b.block.get_forecast_data(date_bult,fcst_parameters,villes,echeances)
            
            if len(fcst_data) == 0 :
                error_msg.append('Prévision indisponible')
                continue

            echeances_obj = sorted(echeances_obj, key=lambda hh: hh.end)
            jours = generate_echeances_dict(date_bult, echeances_obj)
            villes = sorted(villes, key=lambda st: st.name)
            fcst_parameters = sorted(fcst_parameters, key=lambda pp: pp.name)
                        
            # z = Station.objects.filter(name=zone).first()
            for z in fcst_data:
                for paramid in fcst_data[z]:
                    pp = fcst_data[z][paramid]
                    paramSN = Variable.objects.get(pk=paramid)
                    if paramSN.shortName=='symbol_code': # traitement spécial de symboles
                        if modify :
                            pp = {ech : (p[0],render_weather_icon_select(name=f"fcst_{z}_{paramid}_{ech}_{p[0]}",selected=p[1])) for ech,p in pp.items()}
                        else :
                            pp = {ech : (p[0],'<img class="weather_icon" src="'+os.path.join('/media','weathericons',f'{p[1]}.png')+'"/>') for ech,p in pp.items()}
                        fcst_data[z][paramid] = pp
               
            block_contexts[b.id] = {
                'fcstT_obs_data': fcst_data,
                'fcstT_sorted_heures': [{'id':hh.id,'name':hh.name} for hh in echeances_obj],
                'fcstT_stations': [{'id':st.id,'name':st.name} for st in villes],
                'fcstT_jours_obs': jours,
                'fcstT_parameters':[{'id':pp.id,'name':pp.name} for pp in fcst_parameters],
                'fcstT_periode': periode
            }
        elif b.block_type in ['ObsTitleTextImageBlock','FcstTitleTextImageBlock','FcstImageBlock','ObsImageBlock']:
            # pprint(b.block_type)
            if b.block_type in ['ObsTitleTextImageBlock','ObsImageBlock']  : typeDir = 'obs_map'
            if b.block_type in ['FcstTitleTextImageBlock','FcstImageBlock'] : typeDir = 'fcst_map'

            mapconfig = b.value['carte']
            echeances = [b.value['echeance']]

            if mapconfig :  identifier = mapconfig.id
            else : identifier = 0
            file_name = f'{identifier}_{typeDir}_{date_bult.strftime("%d%m%Y")}_{echeances[0].echeance}'
            url_img_png = os.path.join('/media','chartmet',typeDir,date_bult.strftime("%Y/%m/%d"),'png',f'{file_name}.png')
            url_img_html = os.path.join('/media','chartmet',typeDir,date_bult.strftime("%Y/%m/%d"),'html',f'{file_name}.html')
            
            output_base_png = os.path.join(settings.MEDIA_ROOT, 'chartmet',typeDir,date_bult.strftime("%Y/%m/%d"),'png',f'{file_name}.png')
            output_base_html = os.path.join(settings.MEDIA_ROOT, 'chartmet',typeDir,date_bult.strftime("%Y/%m/%d"),'html',f'{file_name}.html')

            if (not os.path.exists(output_base_png) or not os.path.exists(output_base_html)) or initialize :
                if identifier==0 : identifier=None
                if typeDir == 'obs_map' : generate_observation_map(date_bult.strftime("%Y-%m-%d"), echeances[0].echeance,identifier)
                if typeDir == 'fcst_map' : generate_forecast_map(date_bult.strftime("%Y-%m-%d"), echeances[0].echeance,identifier)
            if b.block_type in ['ObsTitleTextImageBlock','FcstTitleTextImageBlock']:
                display_periode = b.value['periode']
                periode = format_periode(display_periode,echeances,date_bult)
                data,data_id,param,zone,ech = b.block.get_data(date_bult,b.value)
                block_contexts[b.id] = {
                    'Text': data,
                    'url_img_png':  url_img_png,
                    'url_img_html':  url_img_html,
                    'periode': periode,
                    'fields': {'forecast_id':data_id,'param':param.id,'zone':zone.id,'ech':ech}
                }
            else :
                block_contexts[b.id] = {
                    'url_img_png':  url_img_png,
                    'url_img_html':  url_img_html,
                }
            titre_legende = b.value['titre_legende']
            if titre_legende :
                block_contexts[b.id]['titre_legende'] = 'Figure '+str(figNum)+' : '+titre_legende
                figNum+=1
        elif b.block_type=='TitleTextBlock' :
            echeances = [b.value['echeance']]
            display_periode = b.value['periode']
            periode = format_periode(display_periode,echeances,date_bult)
            
            data,data_id,param,zone,ech = b.block.get_data(date_bult,b.value)
            
            block_contexts[b.id]={
                'Text': data,
                'periode': periode,
                'fields': {'forecast_id':data_id,'param':param.id,'zone':zone.id,'ech':ech}
            }
        elif b.block_type in ['ModelTitleTextImageBlock','ModelImageBlock'] :
            mapconfig = b.value['modelmap']
            param = b.value['model_parametre']
            echeances = [b.value['fentre_calcul']] 
            fct = b.value['fonction']
            modele = b.value['modele']
            if mapconfig == None : id_map=0
            else : id_map = mapconfig.id

            png_file = f'{id_map}_map_model_{fct}_{param}_{date_bult.strftime("%d%m%Y")}_{int(echeances[0].start)}_{int(echeances[0].end)}.png'
            output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'model_map',modele, date_bult.strftime("%Y/%m/%d"), 'png')
            Mfcst_url_img_png = os.path.join('/media', 'chartmet', 'model_map',modele, date_bult.strftime("%Y/%m/%d"), 'png', png_file)
            if not os.path.exists(os.path.join(output_path_png,png_file)) or initialize:
                if mapconfig : cc = generate_model_map(date_bult.strftime("%Y-%m-%d"), echeances[0].start,echeances[0].end,param,function=fct,pk=mapconfig.id,schema=modele)
                else : cc = generate_model_map(date_bult.strftime("%Y-%m-%d"), echeances[0].start,echeances[0].end,param,function=fct,pk=None,schema=modele)
                Mfcst_url_img_png = cc['png']

            if b.block_type=='ModelTitleTextImageBlock':
                display_periode = b.value['periode']
                Mperiode = format_periode(display_periode,echeances,date_bult)
                Mforecast_data,forecast_id,parametre,zone,ech = b.block.get_data(date_bult,b.value)
                block_contexts[b.id] = {
                    'Text': Mforecast_data,
                    'url_img_png': Mfcst_url_img_png,
                    'periode': Mperiode,
                    'fields': {'forecast_id':forecast_id,'param':parametre.id,'zone':zone.id,'ech':ech}
                }
            else :
                block_contexts[b.id] = {
                    'url_img_png': Mfcst_url_img_png
                }
            titre_legende = b.value['titre_legende']
            if titre_legende :
                block_contexts[b.id]['titre_legende'] = 'Figure '+str(figNum)+' : '+titre_legende
                figNum+=1
        elif b.block_type=='TwoCarteModelBlock' :
            carte1 = b.value['carte_1']
            carte2 = b.value['carte_2']
            style={'s1':'','s2':''}
            block_contexts[b.id] ={}
            for i in [1,2]:
                c=b.value[f'carte_{i}']
                style[f's{i}'] = get_style(c)
                mapconfig = c['modelmap']
                param = c['model_parametre']
                echeances = [c['fentre_calcul']] 
                fct = c['fonction']
                modele = c['modele']
                if mapconfig == None : id_map=0
                else : id_map = mapconfig.id

                png_file = f'{id_map}map_model_{fct}_{param}_{date_bult.strftime("%d%m%Y")}_{int(echeances[0].start)}_{int(echeances[0].end)}.png'
                output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'model_map',modele, date_bult.strftime("%Y/%m/%d"), 'png')
                Mfcst_url_img_png = os.path.join('/media', 'chartmet', 'model_map',modele, date_bult.strftime("%Y/%m/%d"), 'png', png_file)
                if not os.path.exists(os.path.join(output_path_png,png_file)) or initialize:
                    if mapconfig : cc = generate_model_map(date_bult.strftime("%Y-%m-%d"), echeances[0].start,echeances[0].end,param,function=fct,pk=mapconfig.id,schema=modele)
                    else : cc = generate_model_map(date_bult.strftime("%Y-%m-%d"), echeances[0].start,echeances[0].end,param,function=fct,pk=None,schema=modele)
                    Mfcst_url_img_png = cc['png']
                
                block_contexts[b.id][f'url_img_png{i}'] = Mfcst_url_img_png
                titre_legende = c['titre_legende']
                if titre_legende :
                    block_contexts[b.id][f'titre_legende{i}'] = 'Figure '+str(figNum)+' : '+titre_legende
                    figNum+=1
        elif b.block_type in ['ObsTitleTextCarteSpatialBlock','CarteSpatialBlock']  :

            mapconfig = b.value['obs_map']
            param = b.value['obs_map'].parametre
            localite = b.value['stations']
            echeance_map = b.value['map_obs'].echeance


            png_file = f'map_points_{localite.id}_{param.name}_{date_bult.strftime("%d%m%Y")}_{echeance_map.echeance}.png'
            output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'points_map',date_bult.strftime("%Y/%m/%d"), 'png')
            MapObs_url_img_png = os.path.join('/media', 'chartmet', 'points_map', date_bult.strftime("%Y/%m/%d"), 'png', png_file)

            if not os.path.exists(os.path.join(output_path_png,png_file))  or initialize:
                if mapconfig : cc = generate_Spatial_points_map(date_bult.strftime("%Y-%m-%d"),localite,pk=mapconfig.id)
                else : cc = generate_Spatial_points_map(date_bult.strftime("%Y-%m-%d"),localite,pk=None)
                MapObs_url_img_png = cc['png']

            if b.block_type=='ObsTitleTextCarteSpatialBlock':
                echeances = [b.value['echeance']]
                display_periode = b.value['periode']
                MapObsperiode = format_periode(display_periode,echeances,date_bult)
                Mapobs_data,obs_id,parametre,zone,ech = b.block.get_data(date_bult,b.value)
                block_contexts[b.id] = {
                    'Text': Mapobs_data,
                    'url_img_png': MapObs_url_img_png,
                    'periode': MapObsperiode,
                    'fields': {'forecast_id':obs_id,'param':parametre.id,'zone':zone.id,'ech':ech}
                }
            else :
                block_contexts[b.id] = {
                    'url_img_png': MapObs_url_img_png
                }
            titre_legende = b.value['obs_map']['titre_legende']
            if titre_legende :
                block_contexts[b.id]['titre_legende'] = 'Figure '+str(figNum)+' : '+titre_legende
                figNum+=1
        elif b.block_type=='TwoCarteSpatialBlock' :
            carte1 = b.value['carte_1']
            carte2 = b.value['carte_2']
            style={'s1':'','s2':''}
            block_contexts[b.id] ={}
            for i in [1,2]:
                c=b.value[f'carte_{i}']
                style[f's{i}'] = get_style(c)
                mapconfig = c['map_obs']
                param = c['map_obs'].parametre
                localite = c['stations']
                echeance_map = c['map_obs'].echeance
                source = 'observation'

                if mapconfig: id_map=mapconfig.id
                else : id_map=None
                png_file = f'{id_map}_Preconfigured_map_points_{localite.id}_{param.name}_{date_bult.strftime("%d%m%Y")}_{echeance_map.echeance}.png'

                output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'points_map',date_bult.strftime("%Y/%m/%d"), 'png')
                MapObs_url_img_png = os.path.join('/media', 'chartmet', 'points_map', date_bult.strftime("%Y/%m/%d"), 'png', png_file)
                if not os.path.exists(os.path.join(output_path_png,png_file)) or initialize :
                    if mapconfig : cc = generate_Spatial_points_map(date_bult.strftime("%Y-%m-%d"),localite,pk=mapconfig.id)
                    else : cc = generate_Spatial_points_map(date_bult.strftime("%Y-%m-%d"),localite,pk=None)
                    MapObs_url_img_png = cc['png']
                block_contexts[b.id][f'url_img_png{i}'] = MapObs_url_img_png
                titre_legende = c['titre_legende']
                if titre_legende :
                    block_contexts[b.id][f'titre_legende{i}'] = 'Figure '+str(figNum)+' : '+titre_legende
                    figNum+=1
        elif b.block_type in ['ObsTitleTextCarteDecadeBlock','CarteDecadeBlock'] :
            mapconfig = b.value['map_obs']
            param,source = b.value['parametre_decade'].split(';')
            fonction = b.value['fonction']
            decade1 = int(b.value['decade1'])-1 # on soustrait 1 car le bulletin est élaboré à la décade suivante de celle du bulletin
            decade2 = int(b.value['decade2'])-1 # donc la décade courante est la décade du bulletin (donc -1)
                
            titre_legende = b.value['titre_legende']
            if mapconfig: id_map=mapconfig.id
            else : id_map=None

            png_file = f'{id_map}_map_decade_{source}_{param}_{fonction}_{decade1}_{decade2}_{date_bult.strftime("%d%m%Y")}.png'
            output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'decades',date_bult.strftime("%Y/%m/%d"), 'png')
            MapObs_url_img_png = os.path.join('/media', 'chartmet', 'decades', date_bult.strftime("%Y/%m/%d"), 'png', png_file)
            
            if not os.path.exists(os.path.join(output_path_png,png_file)) or initialize :
                
                cc = generate_Decadaire_map(date_bult.strftime("%Y-%m-%d"),decade1,decade2,source,param,fonction,pk=id_map)
                MapObs_url_img_png = cc['png']

            if b.block_type == 'ObsTitleTextCarteDecadeBlock':
                echeances = [b.value['echeance']]
                display_periode = b.value['periode']
                MapObsperiode = format_periode(display_periode,echeances,date_bult)
              
                Mapobs_data,obs_id,parametre,zone,ech = b.block.get_data(date_bult,b.value)
                block_contexts[b.id] = {
                    'Text': Mapobs_data,
                    'url_img_png': MapObs_url_img_png,
                    'periode': MapObsperiode,
                    'fields': {'forecast_id':obs_id,'param':parametre.id,'zone':zone.id,'ech':ech}
                }
            else : 
                block_contexts[b.id] = {
                    'url_img_png': MapObs_url_img_png
                }
            titre_legende = b.value['titre_legende']
            if titre_legende :
                block_contexts[b.id]['titre_legende'] = 'Figure '+str(figNum)+' : '+titre_legende
                figNum+=1
        elif b.block_type=='TwoCarteDecadelock' :
            ##########CAS SPECIAL pour TESTER ########################
            # date_obj=datetime.strptime('2025-03-01', "%Y-%m-%d")
            # date_bult = date_obj.date()
            ##########################################################
            ##########################################################
            ##########################################################
            ##########################################################
            carte1 = b.value['carte_1']
            carte2 = b.value['carte_2']
            style={'s1':'','s2':''}
            block_contexts[b.id] ={}
            for i in [1,2]:
                c=b.value[f'carte_{i}']
                style[f's{i}'] = get_style(c)
                mapconfig = c['map_obs']
                param,source = c['parametre_decade'].split(';')
                fonction = c['fonction']
                decade1 = int(c['decade1'])-1 # on soustrait 1 car le bulletin est élaboré à la décade suivante de celle du bulletin
                decade2 = int(c['decade2'])-1 # donc la décade courante est la décade du bulletin (donc -1)
                titre_legende = c['titre_legende']
                if mapconfig: id_map=mapconfig.id
                else : id_map=None

                png_file = f'{id_map}_map_decade_{source}_{param}_{fonction}_{decade1}_{decade2}_{date_bult.strftime("%d%m%Y")}.png'
                output_path_png = os.path.join(settings.MEDIA_ROOT, 'chartmet', 'decades',date_bult.strftime("%Y/%m/%d"), 'png')
                MapObs_url_img_png = os.path.join('/media', 'chartmet', 'decades', date_bult.strftime("%Y/%m/%d"), 'png', png_file)
                # print(f"{decade1},{decade2},{source},{param},{fonction},pk={id_map}")
                # print('-----------------')
                
                if not os.path.exists(os.path.join(output_path_png,png_file)) or initialize :
                    cc = generate_Decadaire_map(date_bult.strftime("%Y-%m-%d"),decade1,decade2,source,param,fonction,pk=id_map)
                    MapObs_url_img_png = cc['png']
                block_contexts[b.id][f'url_img_png{i}'] = MapObs_url_img_png
                if titre_legende :
                    block_contexts[b.id][f'titre_legende{i}'] = 'Figure '+str(figNum)+' : '+titre_legende
                    figNum+=1 
        elif b.block_type in ['ObsTitleTextCarteNDVIBlock','NDVIBlock'] :
            
            type_carte = b.value['type_carte']
            date_decade_precedente = date_bult - timedelta(days=9)# décade précédente à la date du bulletin
            currend_decade = get_current_decade_code(date_decade_precedente) 
            directory = os.path.join('/media','agromet','ndvi',currend_decade)
            abs_path = os.path.join(settings.MEDIA_ROOT,'agromet','ndvi',currend_decade)
            png_file =os.path.join(directory, f'NDVI_{type_carte}.png')
            if not os.path.isfile(os.path.join(abs_path, f'NDVI_{type_carte}.png')):
                print(f"Error: pas de carte ndvi pour la decade {currend_decade}")
                continue
            if b.block_type == 'ObsTitleTextCarteNDVIBlock':
                echeances = [b.value['echeance']]
                Mapobs_data,obs_id,parametre,zone,ech = b.block.get_data(date_bult,b.value)
                block_contexts[b.id] = {
                    'Text': Mapobs_data,
                    'url_img_png': png_file,
                    'fields': {'forecast_id':obs_id,'param':parametre.id,'zone':zone.id,'ech':ech}
                }
            else :
                block_contexts[b.id] = {
                    'url_img_png': png_file
                }
            titre_legende = b.value['titre_legende']
            if titre_legende :
                block_contexts[b.id]['titre_legende'] = 'Figure '+str(figNum)+' : '+titre_legende
                figNum+=1
        elif b.block_type=='BesoinsEauBlock' :
            format_contenu = b.value['format_contenu']
            currend_decade = get_current_decade_code(date_bult)
            directory = os.path.join(settings.MEDIA_ROOT,'agromet','besoins_eau',currend_decade,format_contenu)
            directory_includes = os.path.join('/media','agromet','besoins_eau',currend_decade,format_contenu)
            if not os.path.isdir(directory):
                print("Error: pas de besoins en eau")
                continue
            files = [f for f in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(f'.{format_contenu}')]
            contenu = ""
            if format_contenu =='html':
                html_files = [os.path.join(directory, fo) for fo in files]
                for file_path in html_files:
                    with open(file_path, 'r', encoding='utf-8') as f:
                            contenu += '<div style="'+style['image']+'">'
                            contenu += f.read() + "\n"
                            contenu += '</div>'
            elif format_contenu =='png':
                png_files = [os.path.join(directory_includes, fo) for fo in files]
                for file_path in png_files:
                    contenu += '<div style="'+style['image']+'">'
                    contenu += f'<img src="{file_path}" alt="table besoins en eau" style="max-width: 100%;">'
                    contenu += '</div>'
            else :
                continue
            block_contexts[b.id] = {
                'contenu': contenu
            }
        elif b.block_type=='textImage':
            pass
        if b.id in block_contexts : block_contexts[b.id]['style'] = style

        if b.id in block_contexts and 'texte' in b.value : block_contexts[b.id]['AnnexText']=b.value['texte']

        # end_time = time.time()
        # print(f"Temps d'exécution : {end_time - start_time:.6f} secondes pour {b.block_type}")
    context['object'] = bulletin
    context['errors'] = error_msg
    context['modify_text'] = modify
    context['block_contexts'] = block_contexts
    return context

def get_configured_elements_for_bulletin(bulletin):

    stations = set()
    zones = set()
    parametres = set()
    echeances = set()
    heures  = set()

    zone = set()
    parametre = set()
    echeance = set()

    obsmap = set()
    fcstmap = set()
    modelmap = set()

    result = {}
    for block in bulletin.content:
        value = block.value

        if hasattr(value, 'get'):
            if 'stations' in value:
                stations.update(value['stations'].stations.all())  # Localites de stations
            if 'zone' in value:
                zone.add(value['zone'])  # Station ou Zone
            if 'zones' in value:
                zones.update(value['zones'].villes.all())  # Localites
            if 'parametre' in value:
                parametre.add(value['parametre'])  # Variable
            if 'parametres' in value:
                parametres.update(value['parametres'].parametres.all())  # Parametres
            if 'echeance' in value:
                echeance.add(value['echeance'])  # Echeance
            if 'echeances' in value:
                echeances.update(value['echeances'].echeances.all())  # Echeances
            if 'heures' in value:
                heures.update(value['heures'].echeances.all())  # Heures

            if 'obsmap' in value:
                obsmap = value['obsmap'].id
            if 'fcstmap' in value:
                fcstmap = value['fcstmap'].id
            if 'modelmap' in value:
                modelmap = value['modelmap'].id

    
    result = {
        'stations': list(stations),
        'villes': list(zones),
        'parametres': list(parametres),
        'echeances': list(echeances),
        'heures': list(heures),
        'zone': list(zone),
        'parametre': list(parametre),
        'echeance': list(echeance),
        'obsmap': (obsmap),
        'fcstmap': (fcstmap),
        'modelmap': (modelmap),
    }

    return result

import base64
import re
from bs4 import BeautifulSoup

def embed_images_as_base64(html_str, media_root):
    soup = BeautifulSoup(html_str, "html.parser")

    for img in soup.find_all("img"):
        # pprint(img)
        src = img.get("src", "")
        if src.startswith("data:") or not src:  # déjà en base64 ou vide
            continue

        # Supprimer le préfixe "/media/" et construire le chemin absolu
        relative_path = src.replace("/media/", "")  
        image_path = os.path.join(media_root, relative_path)

        try:
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
                ext = os.path.splitext(image_path)[1].lower().replace(".", "")
                if ext == "jpg":
                    ext = "jpeg"
                mime_type = f"image/{ext}"

                img["src"] = f"data:{mime_type};base64,{encoded}"
        except Exception as e:
            print(f"Erreur lecture image {src}: {e}")

    return str(soup)



