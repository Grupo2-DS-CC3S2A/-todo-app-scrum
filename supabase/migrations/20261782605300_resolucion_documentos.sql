ALTER TABLE tramite_documentario.documentos_tramitados
    ADD COLUMN IF NOT EXISTS motivo_rechazo TEXT NULL,
    ADD COLUMN IF NOT EXISTS fecha_resolucion DATE NULL;

ALTER TABLE tramite_documentario.documentos_tramitados
    ADD CONSTRAINT chk_estado_documento
    CHECK (estado_documento IN ('EN TRAMITE', 'ACEPTADO', 'RECHAZADO'));
