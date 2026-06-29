create extension if not exists "uuid-ossp";

create type estado_solicitud as enum ('Registrada', 'Pendiente', 'EnProceso', 'Respondida', 'Rechazada');

-- 1. DEPENDENCIAS
create table public.dependencias (
    id bigint generated always as identity primary key,
    nombre text not null unique,
    codigo_interno text not null unique
);

insert into public.dependencias (nombre, codigo_interno) values
('Asesoría Legal',         'ALEGAL'),
('Mesa de Partes Central', 'MPARTES'),
('Trámite Documentario',   'TDOC'),
('Recursos Humanos',       'RRHH'),
('Logística',              'LOGIS'),
('Tesorería',              'TESOR'),
('Secretaría General',     'SGEN');

-- 2. PERFILES
-- NOTA: INSERT via service_role_key desde FastAPI (bypass RLS). No agregar política FOR INSERT.
create table public.perfiles (
    id uuid references auth.users on delete cascade primary key,
    nombres text not null,
    apellidos text not null,
    documento_identidad text not null unique,
    rol text not null check (rol in ('admin', 'ciudadano', 'operador')),
    creado_en timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. SOLICITUDES
create table public.solicitudes (
    id uuid default gen_random_uuid() primary key,
    ciudadano_id uuid references public.perfiles(id) on delete restrict not null,
    asunto text not null,
    detalle_solicitud text not null,
    estado estado_solicitud not null default 'Registrada',
    observaciones text default '',
    fecha_registro timestamp with time zone default timezone('utc'::text, now()) not null,
    fecha_ingreso timestamp with time zone,
    fecha_maxima_respuesta timestamp with time zone,
    dependencia_asignada_id bigint references public.dependencias(id),
    actualizado_en timestamp with time zone default timezone('utc'::text, now()) not null
);

-- RLS
alter table public.perfiles enable row level security;
alter table public.solicitudes enable row level security;

-- Políticas para perfiles
create policy "Perfil propio visible"
on public.perfiles for select using (auth.uid() = id);

create policy "Admins y operadores ven todos los perfiles"
on public.perfiles for select using (
    (auth.jwt() -> 'app_metadata' ->> 'rol') in ('admin', 'operador')
);

-- Políticas para solicitudes
create policy "Los ciudadanos ven sus propios trámites"
on public.solicitudes for select using (auth.uid() = ciudadano_id);

create policy "Los administradores y operadores ven todo"
on public.solicitudes for all using (
    exists (select 1 from public.perfiles where perfiles.id = auth.uid() and perfiles.rol in ('admin', 'operador'))
);

create policy "Los ciudadanos pueden crear solicitudes"
on public.solicitudes for insert with check (auth.uid() = ciudadano_id);

-- 4. USUARIOS (auth propia con bcrypt+JWT e independiente de Supabase-Auth)
create table public.usuarios (
    id            text primary key,
    username      text not null unique,
    password_hash text not null,
    rol           text not null check (rol in ('admin', 'operador', 'ciudadano')),
    created_at    timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.usuarios enable row level security;

-- 5. CITIZENS
-- Migración exacta de validation.db (CA-3). Acceso solo via service_role_key desde FastAPI.
create table public.citizens (
    dni        varchar(8)   primary key,
    digit      integer      not null,
    issue_date date         not null,
    firstname  varchar      not null,
    lastname   varchar      not null
);

insert into public.citizens (dni, digit, issue_date, firstname, lastname) values
('40392536', 1, '2024-07-25', 'CESAR',     'LOPEZ ARTEAGA'),
('81000001', 4, '2022-01-14', 'MATEO',     'SALAZAR PAREDES'),
('81000002', 7, '2021-03-09', 'LUCIA',     'RAMIREZ TORRES'),
('81000003', 2, '2020-05-18', 'DIEGO',     'QUISPE HUAMAN'),
('81000004', 9, '2023-07-22', 'VALERIA',   'CASTRO MENDOZA'),
('81000005', 5, '2019-11-05', 'SEBASTIAN', 'ROJAS VARGAS'),
('81000006', 1, '2024-02-12', 'CAMILA',    'FLORES AGUILAR'),
('81000007', 8, '2022-09-30', 'ANDRES',    'MORALES CHAVEZ'),
('81000008', 3, '2021-12-17', 'SOFIA',     'NAVARRO LEON'),
('81000009', 6, '2020-08-26', 'GABRIEL',   'MEDINA SOTO'),
('81000010', 0, '2023-04-03', 'MARIANA',   'CAMPOS REYES'),
('81000011', 9, '2022-06-11', 'NICOLAS',   'PONCE DELGADO'),
('81000012', 2, '2021-10-28', 'ANTONELLA', 'GUTIERREZ SILVA'),
('81000013', 5, '2024-01-19', 'JOAQUIN',   'ESPINOZA RAMOS'),
('81000014', 7, '2019-02-07', 'ISABELLA',  'CORDOVA NUNEZ'),
('81000015', 1, '2020-03-15', 'ALEXANDER', 'VEGA PALACIOS'),
('81000016', 6, '2023-09-01', 'DANIELA',   'HERRERA FUENTES'),
('81000017', 3, '2021-01-25', 'EMILIO',    'VALDEZ ARIAS'),
('81000018', 8, '2022-04-20', 'PAULA',     'IBARRA MEJIA'),
('81000019', 0, '2020-12-02', 'TOMAS',     'BENAVIDES ORTIZ'),
('81000020', 4, '2024-05-27', 'RENATA',    'MIRANDA LOPEZ');

-- RLS para citizens: solo accesible via service_role_key (backend FastAPI). Sin políticas -> sin acceso cliente.
alter table public.citizens enable row level security;

-- Aunque se otorguen acceso a todos, RLS sigue controlando qué filas son visibles.
grant usage on schema public to anon, authenticated, service_role;
grant all on all tables in schema public to anon, authenticated, service_role;
grant all on all sequences in schema public to anon, authenticated, service_role;
