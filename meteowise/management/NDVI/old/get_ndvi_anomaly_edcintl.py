import datetime
import requests
import zipfile
import os

def get_last_complete_pentade():
    today = datetime.date.today()
    year = today.year % 100  # ex: 2025 -> 25
    day_of_year = today.timetuple().tm_yday
    pentade_number = (day_of_year - 1) // 5
    if day_of_year % 5 != 0:
        pentade_number -= 1
    pentade_number += 1
    return year, pentade_number

def build_url_and_names(year, pentade):
    base_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/pentadal/eviirs/ndvi/meananomaly/downloads/pentadal/"

    zip_name = f"wa{year:02d}{pentade:02d}stmean.zip"
    tif_name = f"wa{year:02d}{pentade:02d}stmean.tif"
    tif_namebis = f"wa{year:02d}{pentade:02d}stmeanm.tif"
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
        if tif_name in zip_ref.namelist():
            zip_ref.extract(tif_name, path=output_dir)
            print(f"✅ Fichier extrait : {tif_name}")
            return os.path.join(output_dir, tif_name)
        elif tif_namebis in zip_ref.namelist():
            zip_ref.extract(tif_namebis, path=output_dir)
            print(f"✅ Fichier extrait : {tif_namebis}")
            return os.path.join(output_dir, tif_namebis)
        else:
            print(f"❌ Le fichier {tif_name} et {tif_namebis} n'existent pas dans l'archive.")
            return None
import rasterio
from rasterio.windows import from_bounds
import pandas as pd
import numpy as np

def raster_to_dataframe(tif_path, bbox):
    """
    bbox : (min_lon, min_lat, max_lon, max_lat)
    Retourne un DataFrame avec colonnes : lon, lat, value
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    with rasterio.open(tif_path) as src:
        window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
        window = window.round_offsets().round_lengths()
        data = src.read(1, window=window)  # On lit la première bande
        transform = src.window_transform(window)

        # Obtenir les coordonnées (lon, lat) de chaque pixel
        rows, cols = data.shape
        xs, ys = np.meshgrid(np.arange(cols), np.arange(rows))
        lons, lats = rasterio.transform.xy(transform, ys, xs, offset='center')

        # Aplatir les tableaux et construire le DataFrame
        df = pd.DataFrame({
            'lon': np.array(lons).flatten(),
            'lat': np.array(lats).flatten(),
            'value': data.flatten()
        })

        # Supprimer les pixels sans données (valeurs no-data)
        nodata = src.nodata
        if nodata is not None:
            df = df[df['value'] != nodata]

    return df

# --- Script principal ---
if __name__ == "__main__":
    year, pentade = get_last_complete_pentade()

    url, zip_name, tif_name, tif_namebis = build_url_and_names(year, pentade)

    if download_zip(url, zip_name):
        out_tif = extract_tif(zip_name, tif_name,tif_namebis)
        bbox = (-5.5, 9.0, 2.5, 15.0)  # Burkina Faso approx
        if out_tif :
            df_ndvi = raster_to_dataframe(out_tif, bbox)
            print(df_ndvi.head())
            print(df_ndvi['value'].min())
            print(df_ndvi['value'].max())

