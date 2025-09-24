import datetime
import requests
import zipfile
import os
import rasterio
from rasterio.windows import from_bounds
import pandas as pd
import numpy as np
from datetime import date
from pprint import pprint
def get_previous_decade_code(date_now=None):
    if date_now is not None:
        today = date_now.date()
    else:
        today = date.today()

    day = today.day
    month = today.month
    year = today.year

    # Identifier la décade actuelle
    if day <= 10:
        current_decade = 1
    elif day <= 20:
        current_decade = 2
    else:
        current_decade = 3

    # Passer à la décade précédente
    if current_decade == 1:
        decade = 3
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
    else:
        decade = current_decade - 1

    return f"{decade:02d}{month:02d}{year}"
def get_last_complete_decade():
    today = datetime.date.today()
    year = today.year
    doy = today.timetuple().tm_yday
    last_complete_decade = (doy -1 ) // 10 + 1
    # Reculer de 1 pour prendre la decade précédente
    return (year, last_complete_decade - 1)

def build_url_and_names(year,decade):
    base_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/dekadal/evmodis/ndvi/meananomaly/downloads/dekadal/"

    zip_name = f"wa{year:04d}{decade:02d}ltmean.zip"
    tif_name = f"wa{year:04d}{decade:02d}ltmean.tif"
    tif_namebis = f"wa{year:04d}{decade:02d}ltmeanm.tif"
    return base_url + zip_name, zip_name, tif_name, tif_namebis

def download_zip(url, zip_name):
    print(f"Téléchargement de {zip_name} depuis {url}...")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(zip_name, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print("✅ Téléchargement terminé.")
        return True
    else:
        print(f"❌ Échec du téléchargement : {r.status_code}")
        return False

def extract_tif(zip_name, tif_name, tif_namebis, output_dir="."):
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        for name in [tif_name, tif_namebis]:
            if name in zip_ref.namelist():
                zip_ref.extract(name, path=output_dir)
                print(f"✅ Fichier extrait : {name}")
                return os.path.join(output_dir, name)
        print(f"❌ Aucun fichier tif attendu trouvé dans {zip_name}")
        return None

def raster_to_dataframe(tif_path, bbox):
    min_lon, min_lat, max_lon, max_lat = bbox
    with rasterio.open(tif_path) as src:
        window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
        window = window.round_offsets().round_lengths()
        data = src.read(1, window=window)
        transform = src.window_transform(window)
        rows, cols = data.shape
        xs, ys = np.meshgrid(np.arange(cols), np.arange(rows))
        lons, lats = rasterio.transform.xy(transform, ys, xs, offset='center')
        df = pd.DataFrame({
            'lon': np.array(lons).flatten(),
            'lat': np.array(lats).flatten(),
            'value': data.flatten()
        })
        nodata = src.nodata
        if nodata is not None:
            df = df[df['value'] != nodata]
    return df

# --- Script principal ---
if __name__ == "__main__":
    decadal = get_last_complete_decade()
    bbox = (-5.5, 9.0, 2.5, 15.0)  # Burkina Faso approx
    url, zip_name, tif_name, tif_namebis = build_url_and_names(decadal[0], decadal[1])
    if download_zip(url, zip_name):
        tif_path = extract_tif(zip_name, tif_name, tif_namebis)
        if tif_path:
            df_mean = raster_to_dataframe(tif_path, bbox)
            # df_mean.columns = ['lat', 'lon', 'value']
            # decade = get_previous_decade_code()
            # df_mean['parameter']='ndvi_meananomaly'
            # df_mean['source']='climat'
            # df_mean['decade']=int(decade[:2])
            # df_mean['month']=int(decade[2:4])
            # df_mean['year']=int(decade[-4:])
            # df_mean['name'] = None
            # df_sql = df_mean[['name', 'lon', 'lat', 'decade', 'month', 'year', 'parameter', 'value', 'source']]
            pprint(df_mean)
    else:
        print("❌ Échec : données manquantes pour au moins une des deux pentades.")
