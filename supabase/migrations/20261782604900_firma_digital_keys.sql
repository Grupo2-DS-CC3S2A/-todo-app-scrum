-- ==========================================================
-- FIRMA DIGITAL: BD privada y BD pública lógica
-- ==========================================================

-- [1] En la primera base lógica: public.citizens
-- Se agrega llave privada.
ALTER TABLE public.citizens
ADD COLUMN IF NOT EXISTS llave_privada TEXT;

-- [2] Segunda base lógica: schema firma_publica
CREATE SCHEMA IF NOT EXISTS firma_publica;

-- [3] Misma tabla citizens, pero con llave_publica.
CREATE TABLE IF NOT EXISTS firma_publica.citizens (
    dni            VARCHAR(8) PRIMARY KEY,
    digit          INTEGER NOT NULL,
    issue_date     DATE NOT NULL,
    firstname      VARCHAR NOT NULL,
    lastname       VARCHAR NOT NULL,
    llave_publica  TEXT
);

-- [4] Copia inicial de ciudadanos desde public.citizens.
INSERT INTO firma_publica.citizens (
    dni,
    digit,
    issue_date,
    firstname,
    lastname,
    llave_publica
)
SELECT
    c.dni,
    c.digit,
    c.issue_date,
    c.firstname,
    c.lastname,
    NULL
FROM public.citizens c
ON CONFLICT (dni) DO NOTHING;

-- [5] Tabla de control para asegurar generación única.
CREATE TABLE IF NOT EXISTS public.key_seed_control (
    id          INTEGER PRIMARY KEY DEFAULT 1,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    total_keys  INTEGER NOT NULL,
    CONSTRAINT only_one_seed CHECK (id = 1)
);

GRANT USAGE ON SCHEMA firma_publica TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA firma_publica TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA firma_publica TO anon, authenticated, service_role;