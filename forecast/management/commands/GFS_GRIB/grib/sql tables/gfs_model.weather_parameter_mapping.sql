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
-- Data for Name: weather_parameter_mapping; Type: TABLE DATA; Schema: gfs_model; Owner: -
--

COPY gfs_model.weather_parameter_mapping (id, parameter_name, grib_variable, grib_level, parameter_status, origin_unit, unit, steptype, parameter_description) FROM stdin;
1	acpcp	ACPCP	surface	on	kg.m-2	mm	accum	Convective precipitation (6_Hour Accumulation)
2	tp	APCP	surface	on	kg.m-2	mm	accum	Total precipitation (6_Hour Accumulation)
3	cape	CAPE	surface	on	J/kg	J/kg	instant	Convective available potential energy
4	cprat	CPRAT	surface	on	kg.m-2.s-1	mm/s	instant	Convective precipitation rate
5	crain	CRAIN	surface	off	Code table 4.222	Code table 4.222	instant	Categorical Rain
6	gust	GUST	surface	on	m/s	km/h	instant	Wind speed (gust)
7	lcc	LCDC	low cloud layer	on	%	%	instant	Low cloud cover
8	mcc	MCDC	middle cloud layer	on	%	%	instant	Medium cloud cover
9	prate	PRATE	Surface	on	kg.m-2.s-1	mm/s	instant	Precipitation rate
10	prmsl	PRMSL	mean sea level 	on	Pa	hpa	instant	Pressure reduced to MSL
11	pwat	PWAT	entire atmosphere (considered as a single layer)	on	kg.m-2	mm	instant	Precipitable water
12	2r	RH	2 m above ground	on	%	%	instant	Relative humidity
13	SUNSD	SUNSD	Surface	on	s	s	instant	Sunshine Duration
14	tmax	TMAX	2 m above ground	on	K	C	max	Maximum temperature (6_Hour Maximum)
15	tmin	TMIN	2 m above ground	on	K	C	min	Minimum temperature (6_Hour Minimum)
16	t	TMP	2 m above ground	on	K	C	instant	Temperature
17	veg	VEG	Surface	on	%	%	instant	Vegetation
18	vis	VIS	Surface	on	m	m	instant	Visibility
19	tcc	TCDC	entire atmosphere 	on	%	%	instant	Total cloud cover
20	10u	UGRD	10 m above ground	on	m/s	km/h	instant	u-component of wind
21	10v	VGRD	10 m above ground	on	m/s	km/h	instant	v-component of wind
\.


--
-- Name: weather_parameter_mapping_id_seq; Type: SEQUENCE SET; Schema: gfs_model; Owner: -
--

SELECT pg_catalog.setval('gfs_model.weather_parameter_mapping_id_seq', 13, true);


--
-- PostgreSQL database dump complete
--

