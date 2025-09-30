--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

-- Started on 2025-09-06 11:42:30

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5 (class 2615 OID 17017)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 4930 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 17046)
-- Name: clientes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clientes (
    id_cliente text NOT NULL,
    nombre text NOT NULL,
    categoria text,
    telefono text,
    correo text,
    rfc text,
    calle text,
    numero_exterior text,
    numero_interior text,
    colonia text,
    codigo_postal text,
    municipio text,
    estado text,
    notas text
);


ALTER TABLE public.clientes OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 17061)
-- Name: cotizaciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cotizaciones (
    id_cotizacion integer NOT NULL,
    fecha date NOT NULL,
    valido_hasta date NOT NULL,
    cliente_id text,
    atendido_por text,
    notas text,
    fecha_hora_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    creado_por text,
    tipo text DEFAULT 'Cotización'::text,
    estatus text DEFAULT 'En proceso'::text
);


ALTER TABLE public.cotizaciones OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 17060)
-- Name: cotizaciones_id_cotizacion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cotizaciones_id_cotizacion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cotizaciones_id_cotizacion_seq OWNER TO postgres;

--
-- TOC entry 4932 (class 0 OID 0)
-- Dependencies: 221
-- Name: cotizaciones_id_cotizacion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cotizaciones_id_cotizacion_seq OWNED BY public.cotizaciones.id_cotizacion;


--
-- TOC entry 224 (class 1259 OID 17080)
-- Name: detalle_cotizacion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detalle_cotizacion (
    id_detalle integer NOT NULL,
    id_cotizacion integer,
    id_producto text,
    descripcion text,
    cantidad integer,
    precio_unitario numeric(10,2),
    total numeric(12,2),
    aplica_iva boolean DEFAULT false
);


ALTER TABLE public.detalle_cotizacion OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 17079)
-- Name: detalle_cotizacion_id_detalle_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.detalle_cotizacion_id_detalle_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalle_cotizacion_id_detalle_seq OWNER TO postgres;

--
-- TOC entry 4933 (class 0 OID 0)
-- Dependencies: 223
-- Name: detalle_cotizacion_id_detalle_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.detalle_cotizacion_id_detalle_seq OWNED BY public.detalle_cotizacion.id_detalle;


--
-- TOC entry 228 (class 1259 OID 17125)
-- Name: detalle_pedido; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detalle_pedido (
    id_detalle integer NOT NULL,
    id_pedido integer NOT NULL,
    id_producto character varying(20),
    descripcion text NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(10,2),
    total numeric(10,2)
);


ALTER TABLE public.detalle_pedido OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 17124)
-- Name: detalle_pedido_id_detalle_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.detalle_pedido_id_detalle_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detalle_pedido_id_detalle_seq OWNER TO postgres;

--
-- TOC entry 4934 (class 0 OID 0)
-- Dependencies: 227
-- Name: detalle_pedido_id_detalle_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.detalle_pedido_id_detalle_seq OWNED BY public.detalle_pedido.id_detalle;


--
-- TOC entry 226 (class 1259 OID 17100)
-- Name: pedidos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pedidos (
    id_pedido integer NOT NULL,
    id_cotizacion integer NOT NULL,
    cliente_id character varying(20) NOT NULL,
    creado_por character varying(20) NOT NULL,
    fecha_creacion date DEFAULT CURRENT_DATE NOT NULL,
    fecha_entrega date NOT NULL,
    notas text
);


ALTER TABLE public.pedidos OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 17099)
-- Name: pedidos_id_pedido_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pedidos_id_pedido_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pedidos_id_pedido_seq OWNER TO postgres;

--
-- TOC entry 4935 (class 0 OID 0)
-- Dependencies: 225
-- Name: pedidos_id_pedido_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pedidos_id_pedido_seq OWNED BY public.pedidos.id_pedido;


--
-- TOC entry 218 (class 1259 OID 17027)
-- Name: produccion_lotes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.produccion_lotes (
    id_lote text NOT NULL,
    turno text NOT NULL,
    bolsas_5kg integer DEFAULT 0,
    bolsas_15kg integer DEFAULT 0,
    total_kg integer,
    observaciones text,
    fecha_hora_registro timestamp with time zone DEFAULT now() NOT NULL,
    tiempo_congelacion_s integer DEFAULT 0 NOT NULL,
    tiempo_defrost_s integer DEFAULT 0 NOT NULL,
    CONSTRAINT produccion_lotes_tiempo_congelacion_s_check CHECK ((tiempo_congelacion_s >= 0)),
    CONSTRAINT produccion_lotes_tiempo_defrost_s_check CHECK ((tiempo_defrost_s >= 0))
);


ALTER TABLE public.produccion_lotes OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 17053)
-- Name: productos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.productos (
    id_producto text NOT NULL,
    nombre text,
    descripcion text,
    precio_sugerido numeric(10,2)
);


ALTER TABLE public.productos OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 17018)
-- Name: rrhh_empleados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rrhh_empleados (
    id_empleado text NOT NULL,
    nombre text NOT NULL,
    puesto text,
    nss text,
    activo boolean DEFAULT true,
    calle text,
    numero_exterior text,
    numero_interior text,
    colonia text,
    codigo_postal text,
    municipio text,
    estado text,
    correo_personal text,
    correo_inst text,
    password_hash text
);


ALTER TABLE public.rrhh_empleados OWNER TO postgres;

--
-- TOC entry 4732 (class 2604 OID 17064)
-- Name: cotizaciones id_cotizacion; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cotizaciones ALTER COLUMN id_cotizacion SET DEFAULT nextval('public.cotizaciones_id_cotizacion_seq'::regclass);


--
-- TOC entry 4736 (class 2604 OID 17083)
-- Name: detalle_cotizacion id_detalle; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_cotizacion ALTER COLUMN id_detalle SET DEFAULT nextval('public.detalle_cotizacion_id_detalle_seq'::regclass);


--
-- TOC entry 4740 (class 2604 OID 17128)
-- Name: detalle_pedido id_detalle; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_pedido ALTER COLUMN id_detalle SET DEFAULT nextval('public.detalle_pedido_id_detalle_seq'::regclass);


--
-- TOC entry 4738 (class 2604 OID 17103)
-- Name: pedidos id_pedido; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos ALTER COLUMN id_pedido SET DEFAULT nextval('public.pedidos_id_pedido_seq'::regclass);


--
-- TOC entry 4915 (class 0 OID 17046)
-- Dependencies: 219
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (id_cliente, nombre, categoria, telefono, correo, rfc, calle, numero_exterior, numero_interior, colonia, codigo_postal, municipio, estado, notas) FROM stdin;
\.


--
-- TOC entry 4918 (class 0 OID 17061)
-- Dependencies: 222
-- Data for Name: cotizaciones; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cotizaciones (id_cotizacion, fecha, valido_hasta, cliente_id, atendido_por, notas, fecha_hora_creacion, creado_por, tipo, estatus) FROM stdin;
\.


--
-- TOC entry 4920 (class 0 OID 17080)
-- Dependencies: 224
-- Data for Name: detalle_cotizacion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detalle_cotizacion (id_detalle, id_cotizacion, id_producto, descripcion, cantidad, precio_unitario, total, aplica_iva) FROM stdin;
\.


--
-- TOC entry 4924 (class 0 OID 17125)
-- Dependencies: 228
-- Data for Name: detalle_pedido; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detalle_pedido (id_detalle, id_pedido, id_producto, descripcion, cantidad, precio_unitario, total) FROM stdin;
\.


--
-- TOC entry 4922 (class 0 OID 17100)
-- Dependencies: 226
-- Data for Name: pedidos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pedidos (id_pedido, id_cotizacion, cliente_id, creado_por, fecha_creacion, fecha_entrega, notas) FROM stdin;
\.


--
-- TOC entry 4914 (class 0 OID 17027)
-- Dependencies: 218
-- Data for Name: produccion_lotes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.produccion_lotes (id_lote, turno, bolsas_5kg, bolsas_15kg, total_kg, observaciones, fecha_hora_registro, tiempo_congelacion_s, tiempo_defrost_s) FROM stdin;
250905-02	M	7	2	65	\N	2025-09-05 12:21:00-06	0	0
250905-03	M	8	2	70	\N	2025-09-05 12:46:00-06	0	0
250905-04	M	2	4	70	\N	2025-09-05 13:17:00-06	0	0
250905-05	M	10	1	65	\N	2025-09-05 13:43:00-06	0	0
250905-06	V	13	0	65	\N	2025-09-05 14:15:00-06	0	0
250905-07	V	9	0	45	\N	2025-09-05 16:30:00-06	0	0
250905-08	V	10	0	50	\N	2025-09-05 16:55:00-06	0	0
250905-09	V	7	1	50	\N	2025-09-05 17:27:00-06	0	0
250905-10	V	10	1	65	\N	2025-09-05 17:50:00-06	0	0
250905-11	V	5	3	70	\N	2025-09-05 18:23:00-06	0	0
250905-12	V	7	2	65	\N	2025-09-05 19:00:00-06	0	0
250905-01	M	13	0	65	\N	2025-09-05 00:15:18.991589-06	0	0
\.


--
-- TOC entry 4916 (class 0 OID 17053)
-- Dependencies: 220
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.productos (id_producto, nombre, descripcion, precio_sugerido) FROM stdin;
BR5KG	Bolsa 5kg	Bolsa de hielo de 5 kilogramos	25.00
BR15KG	Bolsa 15kg	Bolsa de hielo de 15 kilogramos	45.00
\.


--
-- TOC entry 4913 (class 0 OID 17018)
-- Dependencies: 217
-- Data for Name: rrhh_empleados; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rrhh_empleados (id_empleado, nombre, puesto, nss, activo, calle, numero_exterior, numero_interior, colonia, codigo_postal, municipio, estado, correo_personal, correo_inst, password_hash) FROM stdin;
CHILL001	Leonardo Galileo Plascencia Gomez	Ingeniero Mecánico	\N	t	Av. Paseo de las Caobas	3320	34	\N	45188	Zapopan	Jalisco	galileoplascencia12@gmail.com	galileo.plascencia@chillice.com.mx	$2b$12$vftkPvTsvJGf6v3BNrOLvecWW0HL3H9eEY34JH1eioNrgPVYw0LXG
\.


--
-- TOC entry 4936 (class 0 OID 0)
-- Dependencies: 221
-- Name: cotizaciones_id_cotizacion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cotizaciones_id_cotizacion_seq', 48, true);


--
-- TOC entry 4937 (class 0 OID 0)
-- Dependencies: 223
-- Name: detalle_cotizacion_id_detalle_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detalle_cotizacion_id_detalle_seq', 50, true);


--
-- TOC entry 4938 (class 0 OID 0)
-- Dependencies: 227
-- Name: detalle_pedido_id_detalle_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detalle_pedido_id_detalle_seq', 12, true);


--
-- TOC entry 4939 (class 0 OID 0)
-- Dependencies: 225
-- Name: pedidos_id_pedido_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pedidos_id_pedido_seq', 12, true);


--
-- TOC entry 4748 (class 2606 OID 17052)
-- Name: clientes clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id_cliente);


--
-- TOC entry 4752 (class 2606 OID 17068)
-- Name: cotizaciones cotizaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cotizaciones
    ADD CONSTRAINT cotizaciones_pkey PRIMARY KEY (id_cotizacion);


--
-- TOC entry 4754 (class 2606 OID 17087)
-- Name: detalle_cotizacion detalle_cotizacion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_cotizacion
    ADD CONSTRAINT detalle_cotizacion_pkey PRIMARY KEY (id_detalle);


--
-- TOC entry 4758 (class 2606 OID 17132)
-- Name: detalle_pedido detalle_pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_pedido
    ADD CONSTRAINT detalle_pedido_pkey PRIMARY KEY (id_detalle);


--
-- TOC entry 4756 (class 2606 OID 17108)
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id_pedido);


--
-- TOC entry 4746 (class 2606 OID 17035)
-- Name: produccion_lotes produccion_lotes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.produccion_lotes
    ADD CONSTRAINT produccion_lotes_pkey PRIMARY KEY (id_lote);


--
-- TOC entry 4750 (class 2606 OID 17059)
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id_producto);


--
-- TOC entry 4744 (class 2606 OID 17025)
-- Name: rrhh_empleados rrhh_empleados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rrhh_empleados
    ADD CONSTRAINT rrhh_empleados_pkey PRIMARY KEY (id_empleado);


--
-- TOC entry 4759 (class 2606 OID 17074)
-- Name: cotizaciones cotizaciones_atendido_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cotizaciones
    ADD CONSTRAINT cotizaciones_atendido_por_fkey FOREIGN KEY (atendido_por) REFERENCES public.rrhh_empleados(id_empleado);


--
-- TOC entry 4760 (class 2606 OID 17069)
-- Name: cotizaciones cotizaciones_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cotizaciones
    ADD CONSTRAINT cotizaciones_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id_cliente);


--
-- TOC entry 4761 (class 2606 OID 17141)
-- Name: cotizaciones cotizaciones_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cotizaciones
    ADD CONSTRAINT cotizaciones_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.rrhh_empleados(id_empleado);


--
-- TOC entry 4762 (class 2606 OID 17088)
-- Name: detalle_cotizacion detalle_cotizacion_id_cotizacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_cotizacion
    ADD CONSTRAINT detalle_cotizacion_id_cotizacion_fkey FOREIGN KEY (id_cotizacion) REFERENCES public.cotizaciones(id_cotizacion);


--
-- TOC entry 4763 (class 2606 OID 17093)
-- Name: detalle_cotizacion detalle_cotizacion_id_producto_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_cotizacion
    ADD CONSTRAINT detalle_cotizacion_id_producto_fkey FOREIGN KEY (id_producto) REFERENCES public.productos(id_producto);


--
-- TOC entry 4767 (class 2606 OID 17133)
-- Name: detalle_pedido detalle_pedido_id_pedido_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detalle_pedido
    ADD CONSTRAINT detalle_pedido_id_pedido_fkey FOREIGN KEY (id_pedido) REFERENCES public.pedidos(id_pedido) ON DELETE CASCADE;


--
-- TOC entry 4764 (class 2606 OID 17114)
-- Name: pedidos pedidos_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id_cliente);


--
-- TOC entry 4765 (class 2606 OID 17119)
-- Name: pedidos pedidos_creado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_creado_por_fkey FOREIGN KEY (creado_por) REFERENCES public.rrhh_empleados(id_empleado);


--
-- TOC entry 4766 (class 2606 OID 17109)
-- Name: pedidos pedidos_id_cotizacion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_id_cotizacion_fkey FOREIGN KEY (id_cotizacion) REFERENCES public.cotizaciones(id_cotizacion) ON DELETE SET NULL;


--
-- TOC entry 4931 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


-- Completed on 2025-09-06 11:42:30

--
-- PostgreSQL database dump complete
--

