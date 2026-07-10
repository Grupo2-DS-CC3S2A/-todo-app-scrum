-- ==========================================================
-- CONTROL DE ACCESO: alcance por dependencia para el rol operador
-- ==========================================================
-- Texto libre (igual que dependencias.nombre y documentos_tramitados.dependencia,
-- ninguna de las dos es un enum en base de datos). NULL para admin/ciudadano,
-- que no estan acotados a una sola dependencia.

ALTER TABLE public.usuarios
ADD COLUMN IF NOT EXISTS dependencia_asignada TEXT NULL;
