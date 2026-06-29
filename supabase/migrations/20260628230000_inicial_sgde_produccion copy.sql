create extension if not exists "uuid-ossp";

create type estado_solicitud as enum ('Registrada', 'Pendiente', 'EnProceso', 'Respondida', 'Rechazada');

-- 1. DEPENDENCIAS
create table public.dependencias (
    id bigint generated always as identity primary key,
    nombre text not null unique,
    codigo_interno text not null unique
);

insert into public.dependencias (nombre, codigo_interno) values
('AsesorÃ­a Legal',         'ALEGAL'),
('Mesa de Partes Central', 'MPARTES'),
('TrÃ¡mite Documentario',   'TDOC'),
('Recursos Humanos',       'RRHH'),
('LogÃ­stica',              'LOGIS'),
('TesorerÃ­a',              'TESOR'),
('SecretarÃ­a General',     'SGEN');

-- 2. PERFILES
create table public.perfiles (
    id uuid references auth.users on delete cascade primary key,
    nombres text not null,
on public.perfiles for select using (
    (auth.jwt() -> 'app_metadata' ->> 'rol') in ('admin', 'operador')
);

create policy "Los ciudadanos ven sus propios trÃ¡mites"
on public.solicitudes for select using (auth.uid() = ciudadano_id);

create policy "Los administradores y operadores ven todo"
on public.solicitudes for all using (
    exists (select 1 from public.perfiles where perfiles.id = auth.uid() and perfiles.rol in ('admin', 'operador'))
);

create policy "Los ciudadanos pueden crear solicitudes"
on public.solicitudes for insert with check (auth.uid() = ciudadano_id);