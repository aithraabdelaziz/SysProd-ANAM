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
-- Data for Name: environmental_configuration; Type: TABLE DATA; Schema: gfs_model; Owner: -
--

COPY gfs_model.environmental_configuration (id, levels, bbox_toplat, bbox_leftlon, bbox_rightlon, bbox_bottomlat, download_grib, download_csv) FROM stdin;
1	{lev_2_m_above_ground,lev_surface,lev_mean_sea_level,lev_entire_atmosphere_(considered_as_a_single_layer),lev_low_cloud_layer,lev_middle_cloud_layer,lev_entire_atmosphere_(considered_as_a_single_layer),lev_entire_atmosphere,lev_10_m_above_ground}	17	-5.5	4	9.4	on	on
\.


--
-- Name: environmental_configuration_id_seq; Type: SEQUENCE SET; Schema: gfs_model; Owner: -
--

SELECT pg_catalog.setval('gfs_model.environmental_configuration_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

