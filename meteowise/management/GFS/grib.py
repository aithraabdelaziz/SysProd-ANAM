import requests
import pygrib
import pandas as pd
import os
import folium
import geopandas as gpd
from shapely.geometry import Point
import tempfile
import yaml
from urllib.parse import urlencode
import argparse
from datetime import datetime
import psycopg2
import shutil
import json
import os

def load_config(config_path=None):
    if config_path is None:
        pathdata = os.path.dirname(os.path.abspath(__file__))
        config_path=os.path.join(pathdata,'config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_db_connection(db_config):
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password']
    )

def load_parameters_from_db(db_config):
    conn = None
    try:
        conn = get_db_connection(db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT parameter_name, parameter_status, grib_variable FROM gfs_model.weather_parameter_mapping")
        rows = cursor.fetchall()
        parameters_config = {row[0]: row[1] for row in rows}
        grib_variables = [row[2] for row in rows if row[1] == 'on']
        name_to_gribvar = {row[0]: row[2] for row in rows if row[1] == 'on'}
        return parameters_config, grib_variables, name_to_gribvar
    finally:
        if conn:
            conn.close()

def load_environmental_config(db_config):
    conn = None
    try:
        conn = get_db_connection(db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT levels, bbox_toplat, bbox_leftlon, bbox_rightlon, bbox_bottomlat, 
                   download_grib, download_csv 
            FROM gfs_model.environmental_configuration LIMIT 1
        """)
        row = cursor.fetchone()
        levels = row[0]
        bbox = {"toplat": row[1], "leftlon": row[2], "rightlon": row[3], "bottomlat": row[4]}
        return levels, bbox, row[5], row[6]
    finally:
        if conn:
            conn.close()

def build_grib_url(grib_cfg):
    base_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
    date = grib_cfg.get("date")
    cycle = grib_cfg.get("cycle", "00")
    forecast_hour = grib_cfg.get("forecast_hour", "000")
    pathdata = os.path.dirname(os.path.abspath(__file__))
    dir_path = f"/gfs.{date}/{cycle}/atmos"
    file_name = f"gfs.t{cycle}z.pgrb2.0p25.f{forecast_hour}"

    query = {
        "dir": dir_path,
        "file": file_name,
        "subregion": ""
    }

    for var in grib_cfg.get("grib_variables", []):
        query[f"var_{var}"] = "on"
    for level in grib_cfg.get("levels", []):
        query[level] = "on"

    query.update(grib_cfg.get("bbox", {}))
    return base_url + "?" + urlencode(query, doseq=True)

def download_grib_file(url, save_to_disk=False):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download GRIB file: HTTP {response.status_code}")
    
    if save_to_disk:
        path = 'grib_temp_data.grib'
        with open(path, 'wb') as f:
            f.write(response.content)
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.grib') as tmp_file:
            tmp_file.write(response.content)
            path = tmp_file.name
    return path

def extract_grib_data(grib_path, parameters_config):
    try:
        grbs = pygrib.open(grib_path)
        grb = grbs.message(1)  # ou utilise `.select()` pour un filtrage plus précis
        # Métadonnées principales
        print(f"Nom complet       : {grb.name}")
        print(f"Nom court         : {grb.shortName}")
        print(f"Unité             : {grb.units}")
        print(f"Niveau            : {grb.level} ({grb.typeOfLevel})")
        print(f"Date de validité  : {grb.validDate}")
        print(f"Pas de temps      : {grb.stepRange} ({grb.stepType})")
        print(f"Dimensions        : {grb.Ni} x {grb.Nj} points")
        print(f"Valeurs min/max   : {grb.values.min()} / {grb.values.max()}")
        print(grb.stepRange)     # → "12-18"
        print(grb.stepType) 

    except Exception as e:
        print(f"[ERROR] Error opening GRIB file: {e}")
        return pd.DataFrame()

    # On affiche les informations des messages
    for grb in grbs:
        print(f" - {grb.name} (shortName: {grb.shortName}, level: {grb.level}, type: {grb.typeOfLevel})")
    grbs.seek(0)  # Revenir au début pour le reste du traitement

    params = [param for param, state in parameters_config.items() if state == 'on']
    df = pd.DataFrame()

    for param in params:
        try:
            # Sélectionner les messages correspondants au paramètre
            specific_grb = grbs.select(shortName=param)
            if not specific_grb:
                print(f"[SKIP] Aucun message trouvé pour {param}")
                continue

            # Pour les paramètres cumulés comme acpcp ou tp, on veut un stepRange de 6h
            if param in ['acpcp', 'tp', 'tmax', 'tmin']:
                selected = None
                for g in specific_grb:
                    try:
                        print(f"Nom complet       : {g.name}")
                        print(f"Nom court         : {g.shortName}")
                        print(f"Unité             : {g.units}")
                        print(f"Niveau            : {g.level} ({g.typeOfLevel})")
                        print(f"Date de validité  : {g.validDate}")
                        print(f"Pas de temps      : {g.stepRange} ({g.stepType})")
                        print(f"Dimensions        : {g.Ni} x {g.Nj} points")
                        print(f"Valeurs min/max   : {g.values.min()} / {g.values.max()}")
                        print(grb.stepRange)     # → "12-18"
                        print(grb.stepType) 
                        start, end = map(int, g.stepRange.split("-"))
                        duration = end - start
                        if duration == 6:
                            selected = g
                            break
                    except Exception:
                        continue
                if selected is None:
                    print(f"[SKIP] Aucun message 6h pour {param}")
                    continue
                grb = selected
            else:
                grb = specific_grb[0]  # Si pas de filtrage particulier, on prend le premier message
                # Métadonnées principales
                print(f"Nom complet       : {grb.name}")
                print(f"Nom court         : {grb.shortName}")
                print(f"Unité             : {grb.units}")
                print(f"Niveau            : {grb.level} ({grb.typeOfLevel})")
                print(f"Date de validité  : {grb.validDate}")
                print(f"Pas de temps      : {grb.stepRange} ({grb.stepType})")
                print(f"Dimensions        : {grb.Ni} x {grb.Nj} points")
                print(f"Valeurs min/max   : {grb.values.min()} / {grb.values.max()}")
                print(grb.stepRange)     # → "12-18"
                print(grb.stepType) 

            data = grb.values
            lats, lons = grb.latlons()

            # Créer les enregistrements pour chaque pixel
            records = [{
                "Latitude": lats[i, j],
                "Longitude": lons[i, j],
                param: data[i, j]
            } for i in range(lats.shape[0]) for j in range(lons.shape[1])]
            
            # Créer un DataFrame pour ce paramètre
            df_param = pd.DataFrame(records)

            # Fusionner ce DataFrame avec le DataFrame final
            df = df_param if df.empty else pd.merge(df, df_param, on=["Latitude", "Longitude"], how="left")

        except (RuntimeError, ValueError) as e:
            print(f"[WARNING] Skipping parameter '{param}': {e}")
            continue

    return df

def convert_units(df):
    df = df.copy()

    #Kelvin -> Celsius
    temp_vars = ['t', 'tmax', 'tmin']
    for var in temp_vars:
        if var in df.columns:
            df[var] = df[var] - 273.15

    #m/s -> km/h
    wind_vars = ['gust', '10u', '10v']
    for var in wind_vars:
        if var in df.columns:
            df[var] = df[var] * 3.6

    #Pa -> hPa
    pressure_vars = ['prmsl']
    for var in pressure_vars:
        if var in df.columns:
            df[var] = df[var] / 100.0

    #kg/m² -> mm
    precip_vars = ['acpcp', 'tp', 'pwat']
    for var in precip_vars:
        if var in df.columns:
            # kg.m-2 est équivalent à mm pour l'eau (1kg/m² = 1mm)
            pass

    #kg.m-2.s-1 -> mm/s (équivalent numériquement)
    rate_vars = ['cprat', 'prate']
    for var in rate_vars:
        if var in df.columns:
            pass

    # Arrondi final
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].round(2)

    return df

def filter_points_by_country(df, shapefile_path, country_name, buffer_km=100):
    if not os.path.exists(shapefile_path):
        print(f"Shapefile path {shapefile_path} does not exist.")
        return gpd.GeoDataFrame()
 
    # Lire le shapefile
    gdf_countries = gpd.read_file(shapefile_path)
 
    # Filtrer le pays
    country_shape = gdf_countries[gdf_countries['NAME'] == country_name]
    if country_shape.empty:
        print(f"Country {country_name} not found in shapefile.")
        return gpd.GeoDataFrame()
 
    gdf_countries = gdf_countries.to_crs(epsg=3395)
    country_shape = gdf_countries[gdf_countries['NAME'] == country_name]
    country_geom = country_shape.geometry.iloc[0]
    country_buffer = country_geom.buffer(buffer_km * 1000)  
 
    geometry = [Point(lon, lat) for lon, lat in zip(df['Longitude'], df['Latitude'])]
    gdf_points = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    gdf_points = gdf_points.to_crs(epsg=3395)
 
    filtered_points = gdf_points[gdf_points.geometry.within(country_buffer)]
    return filtered_points.to_crs("EPSG:4326")

def store_data(conn_config, gdf, name_to_gribvar, date, cycle, forecast_hour):
    conn = get_db_connection(conn_config)
    cursor = conn.cursor()

    for _, row in gdf.iterrows():
        lat = row['Latitude']
        lon = row['Longitude']
        data_json = {}
        try : 

            for param in name_to_gribvar.keys():
                if param in row and pd.notna(row[param]):
                    key = name_to_gribvar[param]
                    data_json[key] = row[param]

            cursor.execute("""
                INSERT INTO gfs_model.weather_data (lat, long, date, cycle, ech, data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (lat, lon, date, cycle, forecast_hour, json.dumps(data_json)))
        except Exception as e :
            print(e)

    conn.commit()
    cursor.close()
    conn.close()


def create_folium_map(gdf_points, output_html):
    m = folium.Map(location=[12.0, -1.5], zoom_start=6)
    for _, row in gdf_points.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=3,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6,
            popup=folium.Popup(
                f"Temp: {row.get('Temperature', 'N/A')}°C<br>Wind: {row.get('Wind speed (gust)', 'N/A')} m/s",
                max_width=300
            )
        ).add_to(m)
    m.save(output_html)
from pprint import pprint
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, default=datetime.utcnow().strftime('%Y%m%d'))
    parser.add_argument('--cycle', type=str, default='00')
    args = parser.parse_args()

    config = load_config()
    db_config = config['database']
    try:
        parameters_config, grib_variables, name_to_gribvar = load_parameters_from_db(db_config)
        levels, bbox, download_grib, download_csv = load_environmental_config(db_config)
        print("[INFO] Configuration loaded from database.")
    except Exception as e:
        print(f"[WARNING] Failed to load from DB: {e}, using config.yaml fallback.")
        parameters_config = config.get('parameters', {})
        levels = config.get('levels', [])
        bbox = config.get('bbox', {})
        grib_variables = config.get('grib_variables', [])
        download_grib = config.get('download_grib', False)
        download_csv = config.get('download_csv', False)

    grib_cfg_base = {
        "grib_variables": grib_variables,
        "levels": levels,
        "bbox": bbox,
        "date": args.date,
        "cycle": args.cycle
    }
    # Create folders
    grib_dir = os.path.join("gfs", args.date, args.cycle)
    csv_dir = os.path.join("csv", args.date, args.cycle)
    html_dir = os.path.join("html", args.date, args.cycle)
    os.makedirs(grib_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    pathdata = os.path.dirname(os.path.abspath(__file__))
    shapefile_path = os.path.join(pathdata,'shapes/ne_110m_admin_0_countries.shp')
    country = 'Burkina Faso'

    for hour in range(0, 240):
        forecast_hour = f"{hour:03d}"
        grib_cfg = grib_cfg_base.copy()
        grib_cfg["forecast_hour"] = forecast_hour


        url = build_grib_url(grib_cfg)
        print(f"[INFO] Downloading GRIB file for hour {forecast_hour}")
        try :
            grib_file_path = download_grib_file(url, save_to_disk=False)
        except Exception as e :
            print(f"[ERROR] Downloading GRIB file for hour {forecast_hour}")
            print(e)

        if download_grib:
            dest_path = os.path.join(grib_dir, f"gfs_{args.date}_{args.cycle}_f{forecast_hour}.grib")
            shutil.move(grib_file_path, dest_path)
            grib_file_path = dest_path
        if not grib_file_path:
            print(f"[WARNING] No data extracted for hour {forecast_hour}")
            continue

        df = extract_grib_data(grib_file_path, parameters_config)
        if df.empty:
            print(f"[WARNING] No data extracted for hour {forecast_hour}")
            continue

        df = convert_units(df)
        filtered_points = filter_points_by_country(df, shapefile_path, country)
        
        store_data(db_config, filtered_points, name_to_gribvar, args.date, args.cycle, forecast_hour)

        if filtered_points.empty:
            print(f"[WARNING] No points found within {country}")
            continue

        if download_csv:
            csv_path = os.path.join(csv_dir, f"grib_{args.date}_{args.cycle}_f{forecast_hour}.csv")
            filtered_points.to_csv(csv_path, index=False)
            print(f"[INFO] Saved CSV to {csv_path}")

        html_path = os.path.join(html_dir, f"grib_map_{args.date}_{args.cycle}_f{forecast_hour}.html")
        create_folium_map(filtered_points, html_path)
        print(f"[INFO] Map saved to {html_path}")

        if not download_grib:
            os.remove(grib_file_path)

if __name__ == "__main__":
    main()
