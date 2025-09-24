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
-- Data for Name: weather_data; Type: TABLE DATA; Schema: gfs_model; Owner: -
--

COPY gfs_model.weather_data (id, lat, long, date, cycle, ech, data) FROM stdin;
\.


--
-- Name: weather_data_id_seq; Type: SEQUENCE SET; Schema: gfs_model; Owner: -
--

SELECT pg_catalog.setval('gfs_model.weather_data_id_seq', 197313, true);


--
-- PostgreSQL database dump complete
--

