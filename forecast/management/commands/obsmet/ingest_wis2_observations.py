import requests
import psycopg2
import json
import yaml
from psycopg2.extras import Json
from datetime import datetime, timedelta

CONFIG_PATH = 'config.yaml'

def load_config(config_path=CONFIG_PATH):
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

def fetch_observations(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. HTTP status: {response.status_code}")
    return response.json().get("features", [])

def process_feature(feature):
    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates", [None, None])

    return {
        "wigos_station_identifier": props.get("wigos_station_identifier"),
        "phenomenon_time": props.get("phenomenonTime"),
        "parameter": props.get("name"),
        "value": props.get("value"),
        "units": props.get("units"),
        "report_time": props.get("reportTime"),
        "latitude": coords[1],
        "longitude": coords[0],
        "data": {
            "parameter": props.get("name"),
            "wigos_station_identifier": props.get("wigos_station_identifier"),
            "units": props.get("units"),
            "phenomenon_time": props.get("phenomenonTime"),
            "value": props.get("value"),
            "coordinates": coords,
            "latitude": coords[1],
            "longitude": coords[0]
        }
    }

def insert_observation(cursor, obs):
    cursor.execute("""
        INSERT INTO wis2.observations (
            wigos_station_identifier, phenomenon_time, parameter,
            value, units, report_time, latitude, longitude, data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (wigos_station_identifier, phenomenon_time, parameter) DO NOTHING;
    """, (
        obs["wigos_station_identifier"], obs["phenomenon_time"], obs["parameter"],
        obs["value"], obs["units"], obs["report_time"],
        obs["latitude"], obs["longitude"], json.dumps(obs["data"])
    ))

def main(report_time=""):
    # Charger la configuration depuis le fichier YAML
    config = load_config()
    db_config = config.get("database")
    api_url = config.get("api", {}).get("url")  # Récupérer l'URL de l'API depuis le fichier YAML
    api_url+=report_time
    if not api_url:
        print("API URL not found in the configuration file.")
        return

    try:
        conn = get_db_connection(db_config)
        cursor = conn.cursor()
        features = fetch_observations(api_url)

        count_inserted = 0
        for feature in features:
            obs = process_feature(feature)

            print(f"Processing: Station={obs['wigos_station_identifier']}, "
                  f"Param={obs['parameter']}, Time={obs['phenomenon_time']}, Value={obs['value']} {obs['units']}")

            insert_observation(cursor, obs)
            if cursor.rowcount > 0:
                print("→ Inserted.")
                count_inserted += 1
            else:
                print("→ Already exists. Skipped.")

        conn.commit()
        print(f"{count_inserted} new observations inserted.")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":

    # start = datetime.fromisoformat("2025-05-12T00:00:00")
    # end = datetime.fromisoformat("2025-05-14T13:00:00")
    end = datetime.now()
    start = (end - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    current = start
    timestamps = []

    while current <= end:
        print(f"==============Traitement de {current} =================")
        report_time = '&reportTime='+current.strftime("%Y-%m-%dT%H:%M:%SZ")
        main(report_time)
        current += timedelta(hours=1)
    
    # main()
    
