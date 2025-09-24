import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pykrige.ok import OrdinaryKriging
from shapely.geometry import Point
from matplotlib.colors import ListedColormap
from cartopy import crs as ccrs
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
from sklearn.metrics import mean_squared_error
from scipy.optimize import curve_fit
from scipy.spatial.distance import pdist, squareform
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error
import os
import pandas as pd
import pandas as pd
from scipy.spatial.distance import pdist, squareform
import geopandas as gpd
import itertools
import openpyxl
import csv
import openmeteo_requests
import requests_cache
from retry_requests import retry
import xarray as xr
import rasterio
from rasterio.transform import from_origin
from retry_requests import retry

from datetime import date, datetime
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

debut = "2025-05-01"
fin = "2025-05-10"

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
sum_et0['name'] = None
df_sql = sum_et0[['name', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]

from sqlalchemy import create_engine
engine = create_engine('postgresql://user@localhost:5432/climforge')
try :
    df_sql.to_sql('decades', schema='climat', con=engine, if_exists='append', index=False, method='multi')
    print("sum_et0 insérée avec succès")
except Exception as e :
    print(f"Error : sum_et0 non insérée")
    pass

mean_et0['parameter']='et0_mean'
mean_et0['source']='gfs_model'
mean_et0['decade']=int(decade[:2])
mean_et0['month']=int(decade[2:4])
mean_et0['year']=int(decade[-4:])
mean_et0['name'] = None
df_sql2 = mean_et0[['name', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]
try :
    df_sql2.to_sql('decades', schema='climat', con=engine, if_exists='append', index=False, method='multi')
    print("mean_et0 insérée avec succès")
except Exception as e :
    print(f"Error : mean_et0 non insérée")
    pass
quit()
# Vérification des valeurs manquantes
print(f"🔍 Nombre de valeurs NaN dans et0_array: {np.isnan(et0_array).sum()}")

# Détermination du nom des fichiers
start_str = start_date.strftime("%Y%m%d")
end_str = end_date.strftime("%Y%m%d")

tiff_filename = f"evapotranspiration_gfs_{start_str}_{end_str}.tif"
nc_filename = f"evapotranspiration_gfs_{start_str}_{end_str}.nc"

# Sauvegarde en GeoTIFF
transform = from_origin(lon_min, lat_max, resolution, resolution)
with rasterio.open(
    tiff_filename,
    "w",
    driver="GTiff",
    height=et0_array.shape[0],
    width=et0_array.shape[1],
    count=1,
    dtype=et0_array.dtype,
    crs="EPSG:4326",
    transform=transform,
) as dst:
    dst.write(et0_array, 1)

print(f"✅ Fichier GeoTIFF enregistré: {tiff_filename}")

# Sauvegarde en NetCDF
ds = xr.Dataset(
    {
        "et0_fao_evapotranspiration": ( ["latitude", "longitude"], et0_array),
    },
    coords={
        "latitude": latitudes,
        "longitude": longitudes,
    },
)
ds.to_netcdf(nc_filename)
print(f"✅ Fichier NetCDF enregistré: {nc_filename}")




