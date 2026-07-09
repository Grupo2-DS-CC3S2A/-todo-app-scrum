-- ==========================================================
-- CONTROL DE ACCESO: ciclo de vida de identidades
-- ==========================================================
-- Permite activar/revocar el acceso de un usuario sin borrar su cuenta,
-- y filtra el login/JWT de cuentas desactivadas.

ALTER TABLE public.usuarios
ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true;
