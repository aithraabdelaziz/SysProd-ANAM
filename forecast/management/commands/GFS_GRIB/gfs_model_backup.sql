--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: gfs_model; Type: SCHEMA; Schema: -; Owner: user
--

CREATE SCHEMA gfs_model;


ALTER SCHEMA gfs_model OWNER TO "user";

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: environmental_configuration; Type: TABLE; Schema: gfs_model; Owner: user
--

CREATE TABLE gfs_model.environmental_configuration (
    id integer NOT NULL,
    levels text[],
    bbox_toplat double precision,
    bbox_leftlon double precision,
    bbox_rightlon double precision,
    bbox_bottomlat double precision,
    download_grib character varying(10) DEFAULT 'on'::character varying,
    download_csv character varying(10) DEFAULT 'on'::character varying
);


ALTER TABLE gfs_model.environmental_configuration OWNER TO "user";

--
-- Name: environmental_configuration_id_seq; Type: SEQUENCE; Schema: gfs_model; Owner: user
--

CREATE SEQUENCE gfs_model.environmental_configuration_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE gfs_model.environmental_configuration_id_seq OWNER TO "user";

--
-- Name: environmental_configuration_id_seq; Type: SEQUENCE OWNED BY; Schema: gfs_model; Owner: user
--

ALTER SEQUENCE gfs_model.environmental_configuration_id_seq OWNED BY gfs_model.environmental_configuration.id;


--
-- Name: weather_data; Type: TABLE; Schema: gfs_model; Owner: user
--

CREATE TABLE gfs_model.weather_data (
    id integer NOT NULL,
    lat double precision,
    long double precision,
    date date,
    cycle text,
    ech integer,
    data jsonb
);


ALTER TABLE gfs_model.weather_data OWNER TO "user";

--
-- Name: weather_data_id_seq; Type: SEQUENCE; Schema: gfs_model; Owner: user
--

CREATE SEQUENCE gfs_model.weather_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE gfs_model.weather_data_id_seq OWNER TO "user";

--
-- Name: weather_data_id_seq; Type: SEQUENCE OWNED BY; Schema: gfs_model; Owner: user
--

ALTER SEQUENCE gfs_model.weather_data_id_seq OWNED BY gfs_model.weather_data.id;


--
-- Name: weather_parameter_mapping; Type: TABLE; Schema: gfs_model; Owner: user
--

CREATE TABLE gfs_model.weather_parameter_mapping (
    id integer NOT NULL,
    parameter_name text NOT NULL,
    grib_variable text NOT NULL,
    grib_level text,
    parameter_status character varying(3),
    origin_unit text,
    unit text,
    CONSTRAINT weather_parameter_mapping_parameter_status_check CHECK (((parameter_status)::text = ANY ((ARRAY['on'::character varying, 'off'::character varying])::text[])))
);


ALTER TABLE gfs_model.weather_parameter_mapping OWNER TO "user";

--
-- Name: weather_parameter_mapping_id_seq; Type: SEQUENCE; Schema: gfs_model; Owner: user
--

CREATE SEQUENCE gfs_model.weather_parameter_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE gfs_model.weather_parameter_mapping_id_seq OWNER TO "user";

--
-- Name: weather_parameter_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: gfs_model; Owner: user
--

ALTER SEQUENCE gfs_model.weather_parameter_mapping_id_seq OWNED BY gfs_model.weather_parameter_mapping.id;


--
-- Name: environmental_configuration id; Type: DEFAULT; Schema: gfs_model; Owner: user
--

ALTER TABLE ONLY gfs_model.environmental_configuration ALTER COLUMN id SET DEFAULT nextval('gfs_model.environmental_configuration_id_seq'::regclass);


--
-- Name: weather_data id; Type: DEFAULT; Schema: gfs_model; Owner: user
--

ALTER TABLE ONLY gfs_model.weather_data ALTER COLUMN id SET DEFAULT nextval('gfs_model.weather_data_id_seq'::regclass);


--
-- Name: weather_parameter_mapping id; Type: DEFAULT; Schema: gfs_model; Owner: user
--

ALTER TABLE ONLY gfs_model.weather_parameter_mapping ALTER COLUMN id SET DEFAULT nextval('gfs_model.weather_parameter_mapping_id_seq'::regclass);


--
-- Data for Name: environmental_configuration; Type: TABLE DATA; Schema: gfs_model; Owner: user
--

COPY gfs_model.environmental_configuration (id, levels, bbox_toplat, bbox_leftlon, bbox_rightlon, bbox_bottomlat, download_grib, download_csv) FROM stdin;
1   {lev_2_m_above_ground,lev_surface,lev_mean_sea_level,lev_entire_atmosphere_(considered_as_a_single_layer)}  17  -5.5    4   9.4 on  on
\.


--
-- Data for Name: weather_parameter_mapping; Type: TABLE DATA; Schema: gfs_model; Owner: user
--

COPY gfs_model.weather_parameter_mapping (id, parameter_name, grib_variable, grib_level, parameter_status, origin_unit, unit) FROM stdin;
5   Temperature TMP lev_surface on  Kelvin  Celsius
6   2 metre temperature TMP lev_2_m_above_ground    off Kelvin  Celsius
3   MSLP (Eta model reduction)  MSLET   lev_mean_sea_level  on  Pa  hPa
4   Surface pressure    PRES    lev_surface on  Pa  hPa
2   Wind speed (gust)   GUST    lev_surface on  m/s m/s
12  Relative humidity   RH  \N  on  %   %
7   2 metre relative humidity   RH  lev_2_m_above_ground    off %   %
11  Precipitable water  PWAT    lev_entire_atmosphere_(considered_as_a_single_layer)    on  kg/m²   mm
1   Visibility  VIS lev_surface on  m   m
8   Precipitation rate  PRATE   lev_surface on  kg/m²/s mm/h
9   Forecast surface roughness  SFCR    lev_surface on  m   m
10  Vegetation  VEG lev_surface on  fraction (0–1)  %
13  Land-sea mask   LAND    lev_surface on  binary (0 = sea, 1 = land)  binary
\.


--
-- Name: environmental_configuration_id_seq; Type: SEQUENCE SET; Schema: gfs_model; Owner: user
--

SELECT pg_catalog.setval('gfs_model.environmental_configuration_id_seq', 1, true);


--
-- Name: weather_data_id_seq; Type: SEQUENCE SET; Schema: gfs_model; Owner: user
--

SELECT pg_catalog.setval('gfs_model.weather_data_id_seq', 44575, true);


--
-- Name: weather_parameter_mapping_id_seq; Type: SEQUENCE SET; Schema: gfs_model; Owner: user
--

SELECT pg_catalog.setval('gfs_model.weather_parameter_mapping_id_seq', 13, true);


--
-- Name: environmental_configuration environmental_configuration_pkey; Type: CONSTRAINT; Schema: gfs_model; Owner: user
--

ALTER TABLE ONLY gfs_model.environmental_configuration
    ADD CONSTRAINT environmental_configuration_pkey PRIMARY KEY (id);


--
-- Name: weather_data weather_data_pkey; Type: CONSTRAINT; Schema: gfs_model; Owner: user
--

ALTER TABLE ONLY gfs_model.weather_data
    ADD CONSTRAINT weather_data_pkey PRIMARY KEY (id);


--
-- Name: weather_parameter_mapping weather_parameter_mapping_pkey; Type: CONSTRAINT; Schema: gfs_model; Owner: user
--

ALTER TABLE ONLY gfs_model.weather_parameter_mapping
    ADD CONSTRAINT weather_parameter_mapping_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--