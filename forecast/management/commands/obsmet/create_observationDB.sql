CREATE SCHEMA IF NOT EXISTS wis2;

CREATE TABLE wis2.observations (
    id BIGINT PRIMARY KEY DEFAULT nextval('wis2.observations_id_seq'::regclass),
    wigos_station_identifier TEXT NOT NULL,
    phenomenon_time TEXT NOT NULL,
    parameter TEXT NOT NULL,
    value REAL,
    units TEXT,
    report_time TIMESTAMP WITHOUT TIME ZONE,
    latitude REAL,
    longitude REAL,
    data JSONB,
    CONSTRAINT observations_wigos_station_identifier_phenomenon_time_name_key UNIQUE (wigos_station_identifier, phenomenon_time, parameter)
);

-- Création des index
CREATE INDEX idx_obs_location ON wis2.observations (latitude, longitude);
CREATE INDEX idx_obs_name ON wis2.observations (parameter);
CREATE INDEX idx_obs_time ON wis2.observations (phenomenon_time);

