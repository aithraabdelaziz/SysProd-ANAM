import psycopg2
import yaml


def load_db_config(yaml_file_path: str) -> dict:
    """
    Load database configuration from a YAML file.
    """
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config.get('postgres', {})


def get_db_connection(db_params: dict):
    """
    Establish a connection to the PostgreSQL database using provided parameters.
    """
    try:
        connection = psycopg2.connect(**db_params)
        return connection
    except Exception as error:
        print(f"Error connecting to the database: {error}")
        raise


def insert_vigilance_records(connection):
    """
    Execute the SQL query to insert vigilance records into both target tables.
    """
    base_insert_query = """
    WITH ech_bounds AS (
      SELECT MIN(ech)+1 AS ech_min, MAX(ech) AS ech_max
      FROM gfs_model.weather_data
    ),
    weather_with_day AS (
      SELECT
        w.*,
        (w.date + (w.ech - 1) * interval '1 hour')::date AS weather_day
      FROM gfs_model.weather_data w
      JOIN ech_bounds b ON w.ech BETWEEN b.ech_min AND b.ech_max
    ),
    aggregated_weather AS (
      SELECT
        p.province_id,
        p.province_name,
        w.weather_day,
        MIN((w.data->>'TMIN')::numeric) AS temp_min,
        MAX((w.data->>'TMAX')::numeric) AS temp_max
      FROM weather_with_day w
      JOIN gfs_model.coresp_provinces p
        ON w.lat = p.latitude AND w.long = p.longitude
      GROUP BY p.province_id, p.province_name, w.weather_day
    ),
    threshold_params AS (
      SELECT id_province, param, s0, s1, s2, s3
      FROM vigilances.gfs_seuils
    ),
    vigilance_tmin AS (
      SELECT
        m.province_id,
        m.province_name as zone,
        m.weather_day AS forecast_date,
        'vf' AS param,
        CASE
          WHEN s.s0 IS NULL THEN NULL
          WHEN m.temp_min <= s.s3 THEN 3
          WHEN m.temp_min <= s.s2 THEN 2
          WHEN m.temp_min <= s.s1 THEN 1
          WHEN m.temp_min <= s.s0 THEN 0
          ELSE 0
        END AS level,
        m.temp_min AS value,
        CASE
          WHEN s.s0 IS NULL THEN NULL
          WHEN m.temp_min <= s.s3 THEN s.s2
          WHEN m.temp_min <= s.s2 THEN s.s1
          WHEN m.temp_min <= s.s1 THEN s.s0
          ELSE NULL
        END AS smin,
        CASE
          WHEN s.s0 IS NULL THEN NULL
          WHEN m.temp_min <= s.s3 THEN s.s3
          WHEN m.temp_min <= s.s2 THEN s.s2
          WHEN m.temp_min <= s.s1 THEN s.s1
          WHEN m.temp_min <= s.s0 THEN s.s0
          ELSE s.s0
        END AS smax
      FROM aggregated_weather m
      LEFT JOIN threshold_params s ON s.id_province = m.province_id AND s.param = 'tmin'
    ),
    vigilance_tmax AS (
      SELECT
        m.province_id,
        m.province_name as zone,
        m.weather_day AS forecast_date,
        'vc' AS param,
        CASE
          WHEN s.s0 IS NULL THEN NULL
          WHEN m.temp_max >= s.s3 THEN 3
          WHEN m.temp_max >= s.s2 THEN 2
          WHEN m.temp_max >= s.s1 THEN 1
          WHEN m.temp_max >= s.s0 THEN 0
          ELSE 0
        END AS level,
        m.temp_max AS value,
        CASE
          WHEN s.s0 IS NULL THEN NULL
          WHEN m.temp_max >= s.s3 THEN s.s3
          WHEN m.temp_max >= s.s2 THEN s.s2
          WHEN m.temp_max >= s.s1 THEN s.s1
          WHEN m.temp_max >= s.s0 THEN s.s0
          ELSE s.s0
        END AS smin,
        CASE
          WHEN s.s0 IS NULL THEN NULL
          WHEN m.temp_max >= s.s3 THEN NULL
          WHEN m.temp_max >= s.s2 THEN s.s3
          WHEN m.temp_max >= s.s1 THEN s.s2
          WHEN m.temp_max >= s.s0 THEN s.s1
          ELSE s.s1
        END AS smax
      FROM aggregated_weather m
      LEFT JOIN threshold_params s ON s.id_province = m.province_id AND s.param = 'tmax'
    ),
    combined_vigilance AS (
      SELECT * FROM vigilance_tmin
      UNION ALL
      SELECT * FROM vigilance_tmax
    )
    SELECT
      cv.province_id,
      cv.zone,
      cv.forecast_date,
      cv.param,
      jsonb_build_object(
        'level', level,
        'value', value,
        'smin', smin,
        'smax', smax,
        'zone', zone,
        'start_datetime', to_char(cv.forecast_date, 'YYYY-MM-DD') || 'T00:00',
        'end_datetime', to_char(cv.forecast_date, 'YYYY-MM-DD') || 'T23:59'
      ) AS details,
      mp.geom
    FROM combined_vigilance cv
    LEFT JOIN mask.provinces mp
      ON mp.id = cv.province_id
    ORDER BY cv.province_id, cv.forecast_date, cv.param
    """

    cursor = None
    try:
        cursor = connection.cursor()

        # Insert into vigimet_provinces_auto
        insert_query_auto = f"""
        INSERT INTO gfs_model.vigimet_provinces_auto (
            province_id,
            province_name,
            forecast_date,
            param,
            details,
            geom
        )
        {base_insert_query}
        """
        cursor.execute(insert_query_auto)

        # Insert into vigimet_provinces_prod
        insert_query_prod = f"""
        INSERT INTO gfs_model.vigimet_provinces_prod (
            province_id,
            province_name,
            forecast_date,
            param,
            details,
            geom
        )
        {base_insert_query}
        """
        cursor.execute(insert_query_prod)

        connection.commit()
        print("Data inserted successfully into both tables.")
    except Exception as error:
        print(f"Error during data insertion: {error}")
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


def main():
    config_file_path = "config.yaml"  # Path to your YAML config file
    db_params = load_db_config(config_file_path)

    connection = None
    try:
        connection = get_db_connection(db_params)
        insert_vigilance_records(connection)
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
