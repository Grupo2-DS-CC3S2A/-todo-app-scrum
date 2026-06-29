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
