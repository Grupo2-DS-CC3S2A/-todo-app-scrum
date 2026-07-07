CREATE SCHEMA IF NOT EXISTS tramite_documentario;

CREATE TABLE IF NOT EXISTS tramite_documentario.documentos_tramitados (
    id BIGSERIAL PRIMARY KEY,

    dni VARCHAR(8) NOT NULL,

    nro_documento VARCHAR(5) NOT NULL UNIQUE,

    tipo_documento VARCHAR(20) NOT NULL
        CHECK (tipo_documento IN ('CARTA', 'SOLICITUD', 'OFICIO')),

    dependencia TEXT NOT NULL,

    estado_documento VARCHAR(30) NOT NULL DEFAULT 'EN TRAMITE',

    fecha_tramite DATE NOT NULL DEFAULT CURRENT_DATE,

    fecha_respuesta DATE NOT NULL DEFAULT ((CURRENT_DATE + INTERVAL '30 days')::date),

    contenedor TEXT NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE OR REPLACE FUNCTION tramite_documentario.generar_nro_documento_5()
RETURNS VARCHAR(5)
LANGUAGE plpgsql
AS $$
DECLARE
    v_nro VARCHAR(5);
BEGIN
    LOOP
        v_nro := (10000 + floor(random() * 90000))::INTEGER::TEXT;

        EXIT WHEN NOT EXISTS (
            SELECT 1
            FROM tramite_documentario.documentos_tramitados
            WHERE nro_documento = v_nro
        );
    END LOOP;

    RETURN v_nro;
END;
$$;

ALTER TABLE tramite_documentario.documentos_tramitados
ALTER COLUMN nro_documento SET DEFAULT tramite_documentario.generar_nro_documento_5();

CREATE INDEX IF NOT EXISTS idx_documentos_tramitados_dni
ON tramite_documentario.documentos_tramitados(dni);

CREATE INDEX IF NOT EXISTS idx_documentos_tramitados_dni_tipo_fecha
ON tramite_documentario.documentos_tramitados(dni, tipo_documento, fecha_tramite);

GRANT USAGE ON SCHEMA tramite_documentario TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA tramite_documentario TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA tramite_documentario TO anon, authenticated, service_role;