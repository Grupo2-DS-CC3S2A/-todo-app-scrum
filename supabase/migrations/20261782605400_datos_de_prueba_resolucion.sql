-- ==========================================================
-- DATOS DE PRUEBA: ciclo de resolucion y reemplazo de documentos
-- ==========================================================
-- Usuarios operador de prueba, uno por cada dependencia usada en los
-- tramites de prueba de abajo. Password para ambos: Operador123!
insert into public.usuarios (id, username, password_hash, rol, activo, dependencia_asignada) values
(gen_random_uuid()::text, 'operador_tesoreria', '$2b$12$JSC7Bn5lNq2CFGOIfDhnme/tiWB4Wx2RX6zuLUh/a9SZM8WjGSQfi', 'operador', true, 'Tesorería'),
(gen_random_uuid()::text, 'operador_logistica', '$2b$12$EsuMb16b2hFaPn5sfXP8N.FNbtf0wACm4OeNoYToFqXgxbPffa.jm', 'operador', true, 'Logística');

-- Tramites de prueba: cubren cada estado y los casos limite del ciclo de
-- resolucion/reemplazo. Los DNI usados ya existen en public.citizens
-- (ver 20261782604800_mdp_54_initial_schema.sql).
insert into tramite_documentario.documentos_tramitados
    (dni, tipo_documento, dependencia, contenedor, estado_documento,
     fecha_tramite, fecha_respuesta, motivo_rechazo, fecha_resolucion)
values
-- 1) Pendiente de revision (Tesoreria)
('40392536', 'SOLICITUD', 'Tesorería',
 'http://127.0.0.1:8083/api/documentos/90001/download-signed',
 'EN TRAMITE', CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', NULL, NULL),

-- 2) Aceptado (Tesoreria)
('40392536', 'CARTA', 'Tesorería',
 'http://127.0.0.1:8083/api/documentos/90002/download-signed',
 'ACEPTADO', CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '25 days',
 NULL, CURRENT_DATE - INTERVAL '2 days'),

-- 3) Rechazado dentro del plazo (Tesoreria) -- admite reemplazo
('40392536', 'OFICIO', 'Tesorería',
 'http://127.0.0.1:8083/api/documentos/90003/download-signed',
 'RECHAZADO', CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '10 days',
 'El documento no incluye la firma del representante legal.',
 CURRENT_DATE - INTERVAL '1 day'),

-- 4) Rechazado con el plazo ya vencido (Tesoreria) -- NO admite reemplazo
('81000001', 'SOLICITUD', 'Tesorería',
 'http://127.0.0.1:8083/api/documentos/90004/download-signed',
 'RECHAZADO', CURRENT_DATE - INTERVAL '40 days', CURRENT_DATE - INTERVAL '5 days',
 'El documento presentado no corresponde al tramite solicitado.',
 CURRENT_DATE - INTERVAL '10 days'),

-- 5) Rechazado justo en el limite del plazo (vence hoy) -- limite inclusivo, admite reemplazo
('81000002', 'CARTA', 'Tesorería',
 'http://127.0.0.1:8083/api/documentos/90005/download-signed',
 'RECHAZADO', CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE,
 'Falta adjuntar el anexo requerido.', CURRENT_DATE - INTERVAL '1 day'),

-- 6) Pendiente de revision en otra dependencia (Logistica) -- para probar
--    que un operador de Tesoreria no lo vea ni pueda operar sobre el
('81000003', 'OFICIO', 'Logística',
 'http://127.0.0.1:8083/api/documentos/90006/download-signed',
 'EN TRAMITE', CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', NULL, NULL),

-- 7) Rechazado dentro del plazo en otra dependencia (Logistica)
('81000004', 'SOLICITUD', 'Logística',
 'http://127.0.0.1:8083/api/documentos/90007/download-signed',
 'RECHAZADO', CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '15 days',
 'El numero de documento no es legible.', CURRENT_DATE - INTERVAL '1 day');
