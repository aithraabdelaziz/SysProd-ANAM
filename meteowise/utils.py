import os
from datetime import date, datetime,timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm

import xarray as xr
import cfgrib
import cdsapi

from dateutil.relativedelta import relativedelta

import openmeteo_requests
import requests_cache
from retry_requests import retry

from observation.models import ClimatMois

from pprint import pprint
def get_current_decade_code(date_now=None):
    if date_now is not None : today = date_now.date()
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


def get_mean_sum_et0_gfs():
    # Setup Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)


    # Définition de la zone d'intérêt
    lat_min, lat_max = 9, 16
    lon_min, lon_max = -6, 3
    resolution = 0.25  # Espacement des points

    # Générer la grille de points
    latitudes = np.arange(lat_max, lat_min, -resolution)
    longitudes = np.arange(lon_min, lon_max, resolution)

    # Stockage des résultats
    all_data = []
    et0_array = np.full((len(latitudes), len(longitudes)), np.nan)  # Stockage pour raster

    start_date = None
    end_date = None

    # Boucler sur chaque point de la grille
    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(longitudes):
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "et0_fao_evapotranspiration",
                "forecast_days": 10,
                "models": "gfs_seamless"
            }

            try:
                responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
                response = responses[0]
                
                # Extraire les données journalières
                daily = response.Daily()
                daily_et0_fao_evapotranspiration = daily.Variables(0).ValuesAsNumpy()
                
                dates = pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    periods=len(daily_et0_fao_evapotranspiration),
                    freq="D"
                )
                
                # Vérifier si on obtient bien 10 jours de données
                if len(dates) != 10:
                    print(f"⚠️ Attention : {lat}, {lon} n'a pas retourné 10 jours, mais {len(dates)} jours.")
                    continue
                
                # Stocker les dates pour le nom du fichier
                if start_date is None or dates[0] < start_date:
                    start_date = dates[0]
                if end_date is None or dates[-1] > end_date:
                    end_date = dates[-1]
                
                # Stocker les données
                daily_data = {
                    "lat": lat,
                    "lon": lon,
                    "date": dates,
                    "et0_fao_evapotranspiration": daily_et0_fao_evapotranspiration
                }
                
                df = pd.DataFrame(daily_data)
                all_data.append(df)
                
                # Stocker le **cumul** des 10 jours pour le raster final
                et0_array[i, j] = np.nansum(daily_et0_fao_evapotranspiration)

            except Exception as e:
                print(f"❌ Erreur pour {lat}, {lon}: {e}")

    # Vérification des valeurs récupérées
    if start_date is None or end_date is None:
        print("❌ Erreur : Aucune donnée récupérée, vérifiez l'API.")
        exit()

    print(f"Plage de dates: {start_date} -> {end_date}")
    print(f"Valeurs min/max de l'évapotranspiration cumulée : {np.nanmin(et0_array)}, {np.nanmax(et0_array)}")

    # Concaténer toutes les données en une seule DataFrame
    final_dataframe = pd.concat(all_data, ignore_index=True)

    sum_et0 = final_dataframe.groupby(['lat', 'lon'])['et0_fao_evapotranspiration'].sum().reset_index()
    sum_et0.rename(columns={'et0_fao_evapotranspiration': 'value'}, inplace=True)
    mean_et0 = final_dataframe.groupby(['lat', 'lon'])['et0_fao_evapotranspiration'].mean().reset_index()
    mean_et0.rename(columns={'et0_fao_evapotranspiration': 'value'}, inplace=True)
    decade = get_current_decade_code()
    sum_et0['parameter']='et0_sum'
    sum_et0['source']='gfs_model'
    sum_et0['decade']=int(decade[:2])
    sum_et0['month']=int(decade[2:4])
    sum_et0['year']=int(decade[-4:])
    sum_et0['station'] = None
    df_sql = sum_et0[['station', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]


    mean_et0['parameter']='et0_mean'
    mean_et0['source']='gfs_model'
    mean_et0['decade']=int(decade[:2])
    mean_et0['month']=int(decade[2:4])
    mean_et0['year']=int(decade[-4:])
    mean_et0['station'] = None
    df_sql2 = mean_et0[['station', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]

    return [df_sql,df_sql2]

def get_archive_mean_sum_et0_gfs(debut, fin):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)


    # Définition de la zone d'intérêt
    lat_min, lat_max = 9, 16
    lon_min, lon_max = -6, 3
    resolution = 0.25  # Espacement des points

    # Générer la grille de points
    latitudes = np.arange(lat_max, lat_min, -resolution)
    longitudes = np.arange(lon_min, lon_max, resolution)

    # Stockage des résultats
    all_data = []
    et0_array = np.full((len(latitudes), len(longitudes)), np.nan)  # Stockage pour raster

    start_date = None
    end_date = None

    # Boucler sur chaque point de la grille
    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(longitudes):
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": debut,
                "end_date": fin,
                "daily": "et0_fao_evapotranspiration",
                "models": "gfs_seamless",  # ou ERA5, MERRA2, etc.
                "timezone": "UTC"
            }

            try:
                responses = openmeteo.weather_api("https://archive-api.open-meteo.com/v1/archive", params=params)
                response = responses[0]
                
                # Extraire les données journalières
                daily = response.Daily()
                daily_et0_fao_evapotranspiration = daily.Variables(0).ValuesAsNumpy()
                
                dates = pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    periods=len(daily_et0_fao_evapotranspiration),
                    freq="D"
                )
                print('-',end='')
                
                # Vérifier si on obtient bien 10 jours de données
                # if len(dates) != 10:
                #     print(f"⚠️ Attention : {lat}, {lon} n'a pas retourné 10 jours, mais {len(dates)} jours.")
                #     continue
                
                # Stocker les dates pour le nom du fichier
                if start_date is None or dates[0] < start_date:
                    start_date = dates[0]
                if end_date is None or dates[-1] > end_date:
                    end_date = dates[-1]
                
                # Stocker les données
                daily_data = {
                    "lat": lat,
                    "lon": lon,
                    "date": dates,
                    "et0_fao_evapotranspiration": daily_et0_fao_evapotranspiration
                }
                
                df = pd.DataFrame(daily_data)
                all_data.append(df)
                
                # Stocker le **cumul** des 10 jours pour le raster final
                et0_array[i, j] = np.nansum(daily_et0_fao_evapotranspiration)

            except Exception as e:
                print(f"❌ Erreur pour {lat}, {lon}: {e}")

    # Vérification des valeurs récupérées
    if start_date is None or end_date is None:
        print("❌ Erreur : Aucune donnée récupérée, vérifiez l'API.")
        exit()

    print(f"Plage de dates: {start_date} -> {end_date}")
    print(f"Valeurs min/max de l'évapotranspiration cumulée : {np.nanmin(et0_array)}, {np.nanmax(et0_array)}")

    # Concaténer toutes les données en une seule DataFrame
    final_dataframe = pd.concat(all_data, ignore_index=True)

    sum_et0 = final_dataframe.groupby(['lat', 'lon'])['et0_fao_evapotranspiration'].sum().reset_index()
    sum_et0.rename(columns={'et0_fao_evapotranspiration': 'value'}, inplace=True)
    mean_et0 = final_dataframe.groupby(['lat', 'lon'])['et0_fao_evapotranspiration'].mean().reset_index()
    mean_et0.rename(columns={'et0_fao_evapotranspiration': 'value'}, inplace=True)

    decade = get_current_decade_code(datetime.strptime(debut,"%Y-%m-%d"))

    sum_et0['parameter']='et0_sum'
    sum_et0['source']='gfs_model'
    sum_et0['decade']=int(decade[:2])
    sum_et0['month']=int(decade[2:4])
    sum_et0['year']=int(decade[-4:])
    sum_et0['station'] = None
    df_sql = sum_et0[['station', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]

    mean_et0['parameter']='et0_mean'
    mean_et0['source']='gfs_model'
    mean_et0['decade']=int(decade[:2])
    mean_et0['month']=int(decade[2:4])
    mean_et0['year']=int(decade[-4:])
    mean_et0['station'] = None
    df_sql2 = mean_et0[['station', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]

    return [df_sql,df_sql2]
    
def download_netcdf_era(varias=None, year=None, month=None):
    if varias is None:
        variables = [
            "2m_temperature", "total_precipitation", "10m_wind_speed",
            "high_vegetation_cover", "low_vegetation_cover",
            "potential_evaporation", "evaporation",
            "mean_sea_level_pressure", "2m_dewpoint_temperature"
        ]
    else:
        variables = varias

    now = datetime.now()

    if year is None:
        year = [now.strftime("%Y")]
    if month is None:
        month = [
            (now - relativedelta(months=1)).strftime("%m"),
            (now - relativedelta(months=2)).strftime("%m"),
            (now - relativedelta(months=3)).strftime("%m")
        ]

    dataset = "reanalysis-era5-single-levels-monthly-means"
    netcdfs = []

    for var in variables:
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "variable": [var],
            "year": year,
            "month": month,
            "time": ["00:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": [15.1, -5.6, 9.5, 2.5]
        }

        name_nc = f"{var}_{year[0]}-{month[0]}_{year[-1]}-{month[-1]}.nc"
        print(f"Téléchargement de {name_nc}")
        try:
            client = cdsapi.Client()
            result = client.retrieve(dataset, request)
            result.download(name_nc)
            netcdfs.append(name_nc)
        except Exception as e:
            print(e)

    return netcdfs

def import_netcdf_to_climatmois(nc_path):
    import xarray as xr

    if not os.path.exists(nc_path):
        print(f"[ERREUR] Le fichier {nc_path} est introuvable.")
        return

    try:
        ds = xr.open_dataset(nc_path)
    except Exception as e:
        print(f"[ERREUR] Échec ouverture NetCDF : {e}")
        return

    # Détection automatique de l'axe temporel
    if 'time' in ds.coords:
        times = ds['time'].values
    elif 'valid_time' in ds.coords:
        times = ds['valid_time'].values
    else:
        print("[ERREUR] Aucun axe temporel 'time' ou 'valid_time' trouvé dans le fichier.")
        return
        
    lats = ds.latitude.values
    lons = ds.longitude.values
    short_name = list(ds.data_vars)[0]
    full_name = ds[short_name].attrs.get('long_name', 'inconnu')
    centre = ds.attrs.get('GRIB_centre', 'unknown')

    print(f"Paramètre: {short_name} ({full_name}), Centre: {centre}")
    print(f"Période: {str(times[0])[:10]} à {str(times[-1])[:10]}")

    total_points = len(times) * len(lats) * len(lons)
    print(f"Total de points à traiter : {total_points}")

    bulk = []
    count = 0

    for t_idx, dt in enumerate(tqdm(times, desc="Traitement temps")):
        dt_np = dt if hasattr(dt, 'astype') else np.datetime64(dt)
        year = dt_np.astype('M8[Y]').astype(int) + 1970
        month = dt_np.astype('M8[M]').astype(int) % 12 + 1
        values = ds[short_name].isel(valid_time=t_idx).values

        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                val = float(values[i, j])
                if short_name in ['t2m','d2m']:
                    val -= 273.15
                if short_name in ['tp']:
                    val *= 1000
                if short_name in ['si10']:
                    val *= 3.6
                if short_name in ['sp', 'msl']:
                    val /= 100

                station = f"pt{round(lat, 1)}/{round(lon, 1)}"
                bulk.append(ClimatMois(
                    station=station,
                    lon=round(float(lon), 4),
                    lat=round(float(lat), 4),
                    month=month,
                    year=year,
                    parameter=short_name,
                    name=full_name,
                    value=round(val, 2),
                    source=centre
                ))
                count += 1

                if count % 10000 == 0:
                    for record in bulk:
                        ClimatMois.objects.update_or_create(
                            lon=record.lon,
                            lat=record.lat,
                            month=record.month,
                            year=record.year,
                            parameter=record.parameter,
                            source=record.source,
                            defaults={
                                'station': record.station,
                                'value': record.value,
                                'name': full_name,
                            }
                        )
                    bulk = []

    # Derniers points
    for record in bulk:
        ClimatMois.objects.update_or_create(
            lon=record.lon,
            lat=record.lat,
            month=record.month,
            year=record.year,
            parameter=record.parameter,
            source=record.source,
            defaults={
                'station': record.station,
                'value': record.value,
                'name': full_name,
            }
        )

    print("Import NetCDF terminé.")


def download_grib_era(varias=None,year=None,month=None):

    if varias is None :
        variables = ["2m_temperature","total_precipitation","10m_wind_speed", "high_vegetation_cover",
                "low_vegetation_cover", "potential_evaporation", "evaporation",
                "mean_sea_level_pressure","2m_dewpoint_temperature"]
    else : variables = varias
    now = datetime.now()

    if year is None:
        year = [now.strftime("%Y")]
    if month is None:
        # first_day_this_month = now.replace(day=1)
        # last_month_date = first_day_this_month - timedelta(days=1)
        # month_before_last_date = last_month_date.replace(day=1) - timedelta(days=1)
        month = [
            (now - relativedelta(months=3)).strftime("%m"),
            (now - relativedelta(months=2)).strftime("%m"),
            (now - relativedelta(months=1)).strftime("%m")
        ]
        # month = [(now.replace(day=1) - timedelta(days=1)).strftime("%m")]

    dataset = "reanalysis-era5-single-levels-monthly-means"
    gribs = []
    for var in variables :
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "variable": [var],
            "year": year,
            "month": month,
            "time": ["00:00"],
            "data_format": "grib",
            "download_format": "unarchived",
            "area": [15.1, -5.6, 9.5, 2.5]
        }

        # client = cdsapi.Client()
        # client.retrieve(dataset, request).download()
        name_grib = var+'_'+request["year"][0]+'-'+request["month"][0]+'_'+request["year"][-1]+'-'+request["month"][-1]+'.grib'
        print(f"téléchargement de {name_grib}")
        try :
            client = cdsapi.Client()
            result = client.retrieve(dataset, request)
            result.download(name_grib)
            gribs.append(name_grib)
        except Exception as e :
            print(e)
    return gribs

def import_grib1_to_climatmois(grib_path):
    if not os.path.exists(grib_path):
        print(f"[ERREUR] Le fichier {grib_path} est introuvable.")
        return
    try:
        ds = cfgrib.open_dataset(grib_path, decode_timedelta=True)
    except FileNotFoundError as e:
        print(f"[ERREUR] Fichier introuvable : {e}")
        return
    except OSError as e:
        print(f"[ERREUR] Problème lors de la lecture du GRIB : {e}")
        return
    except Exception as e:
        print(f"[ERREUR] Exception inconnue : {e}")
        return

    short_name = list(ds.data_vars)[0]
    centre = ds.attrs.get('GRIB_centre', 'unknown')
    times = ds.time.values
    lats = ds.latitude.values
    lons = ds.longitude.values
    start_date = str(times[0].astype('M8[D]'))
    end_date = str(times[-1].astype('M8[D]'))
    var = list(ds.data_vars)[0]
    full_name = ds[var].attrs.get('long_name', 'inconnu')
    print(f"Paramètre: {short_name} ({full_name}), Centre: {centre}, Période: {start_date} à {end_date}")

    total_points = len(times) * len(lats) * len(lons)
    print(f"Total de points à traiter : {total_points}")

    bulk = []
    count = 0

    for t_idx, dt in enumerate(tqdm(times, desc="Traitement temps")):
        year = dt.astype('M8[Y]').astype(int) + 1970
        month = dt.astype('M8[M]').astype(int) % 12 + 1

        values = ds[short_name].isel(time=t_idx).values

        for i in range(len(lats)):
            for j in range(len(lons)):
                lat = float(lats[i])
                lon = float(lons[j])
                val = float(values[i, j])
                if short_name in ['t2m','d2m']:
                    val -= 273.15 # conversion température de K à °C
                if short_name in ['tp']:
                    val *= 1000 # conversion pluie de m à mm
                if short_name in ['si10']:
                    val *= 3.6 # conversion vent de m/s à km/h
                if short_name in ['msl']:
                    val /= 100 # conversion pression de Pa à hPa


                station = f"pt{round(lat, 1)}/{round(lon, 1)}"

                bulk.append(ClimatMois(
                    station=station,
                    lon=lon,
                    lat=lat,
                    month=month,
                    year=year,
                    parameter=short_name,
                    name=full_name,
                    value=round(val, 2),
                    source=str(centre)
                ))

                count += 1
                if count % 10000 == 0:
                    # Upsert en lot
                    for record in bulk:
                        ClimatMois.objects.update_or_create(
                            lon=record.lon,
                            lat=record.lat,
                            month=record.month,
                            year=record.year,
                            parameter=record.parameter,
                            source=record.source,
                            defaults={
                                'station': record.station,
                                'value': record.value,
                                'name': full_name,
                            }
                        )
                    bulk = []

    # Insérer ou mettre à jour les restes
    for record in bulk:
        ClimatMois.objects.update_or_create(
            lon=record.lon,
            lat=record.lat,
            month=record.month,
            year=record.year,
            parameter=record.parameter,
            source=record.source,
            defaults={
                'station': record.station,
                'value': record.value,
                'name': full_name,
            }
        )

    print("Import terminé.")

def extract_grib_info(grib_path):
    ds = cfgrib.open_dataset(grib_path, decode_timedelta=True)
    short_name = list(ds.data_vars)[0]
    centre = ds.attrs.get('GRIB_centre', 'unknown')
    times = ds.time.values
    start_date = str(times[0].astype('M8[D]'))
    end_date = str(times[-1].astype('M8[D]'))
    var = list(ds.data_vars)[0]
    full_name = ds[var].attrs.get('long_name', 'inconnu')
    ds.close()
    return {
        'short_name': short_name,
        'full_name': full_name,
        'centre': centre,
        'start_date': start_date,
        'end_date': end_date,
    }

def extract_netcdf_info(nc_path):
    ds = xr.open_dataset(nc_path)

    if not ds.data_vars:
        raise ValueError("Aucune variable trouvée dans le fichier NetCDF.")

    short_name = list(ds.data_vars)[0]
    var = ds[short_name]
    full_name = var.attrs.get('long_name', 'inconnu')
    centre = ds.attrs.get('institution', 'unknown')

    # Détecte un axe temporel
    time_dim = None
    for dim in ds.dims:
        if 'time' in dim.lower():
            time_dim = dim
            break
    if not time_dim:
        raise ValueError("Aucun axe temporel détecté dans le fichier NetCDF.")

    times = ds[time_dim].values
    start_date = str(times[0])[:10]
    end_date = str(times[-1])[:10]

    ds.close()
    return {
        'short_name': short_name,
        'full_name': full_name,
        'centre': centre,
        'start_date': start_date,
        'end_date': end_date,
    }




