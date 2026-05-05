/**
 * Tipos del dominio Mesa de Partes (HU04).
 *
 * Espejan los modelos Pydantic del backend (`src/modelos/solicitud.py`) para
 * evitar drift entre capas.
 */

export const EstadoSolicitud = {
  REGISTRADA: "Registrada",
  PENDIENTE: "Pendiente",
  EN_PROCESO: "EnProceso",
  RESPONDIDA: "Respondida",
  RECHAZADA: "Rechazada",
} as const;

export type EstadoSolicitud =
  (typeof EstadoSolicitud)[keyof typeof EstadoSolicitud];

export const Dependencia = {
  MESA_DE_PARTES: "MesaDePartes",
  TRAMITE_DOCUMENTARIO: "TramiteDocumentario",
  ASESORIA_LEGAL: "AsesoriaLegal",
  RECURSOS_HUMANOS: "RecursosHumanos",
  LOGISTICA: "Logistica",
  TESORERIA: "Tesoreria",
  SECRETARIA_GENERAL: "SecretariaGeneral",
} as const;

export type Dependencia = (typeof Dependencia)[keyof typeof Dependencia];

export interface DependenciaCatalogoItem {
  readonly codigo: Dependencia;
  readonly etiqueta: string;
  readonly plazo_dias_habiles: number;
}

export const CATALOGO_DEPENDENCIAS: readonly DependenciaCatalogoItem[] = [
  { codigo: Dependencia.MESA_DE_PARTES, etiqueta: "Mesa de Partes", plazo_dias_habiles: 3 },
  { codigo: Dependencia.TRAMITE_DOCUMENTARIO, etiqueta: "Tramite Documentario", plazo_dias_habiles: 5 },
  { codigo: Dependencia.ASESORIA_LEGAL, etiqueta: "Asesoria Legal", plazo_dias_habiles: 10 },
  { codigo: Dependencia.RECURSOS_HUMANOS, etiqueta: "Recursos Humanos", plazo_dias_habiles: 7 },
  { codigo: Dependencia.LOGISTICA, etiqueta: "Logistica", plazo_dias_habiles: 5 },
  { codigo: Dependencia.TESORERIA, etiqueta: "Tesoreria", plazo_dias_habiles: 7 },
  { codigo: Dependencia.SECRETARIA_GENERAL, etiqueta: "Secretaria General", plazo_dias_habiles: 5 },
];

export interface Solicitud {
  readonly id: number;
  readonly dni_solicitante: string;
  readonly asunto: string;
  readonly descripcion: string;
  readonly estado: EstadoSolicitud;
  readonly dependencia: Dependencia | null;
  readonly fecha_registro: string;
  readonly fecha_ingreso: string | null;
  readonly fecha_maxima_respuesta: string | null;
  readonly observaciones: string;
}

export interface DerivacionInput {
  readonly dependencia: Dependencia;
  readonly observaciones: string;
}
