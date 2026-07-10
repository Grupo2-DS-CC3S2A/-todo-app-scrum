import { ApiError, type ApiErrorBody } from "@/types/voting";

export type TipoDocumento = "CARTA" | "SOLICITUD" | "OFICIO";

export interface TramiteDb {
  readonly id: number;
  readonly dni: string;
  readonly nro_documento: string;
  readonly tipo_documento: TipoDocumento;
  readonly dependencia: string;
  readonly estado_documento: string;
  readonly fecha_tramite: string;
  readonly fecha_respuesta: string;
  readonly contenedor: string;
  readonly motivo_rechazo?: string | null;
  readonly fecha_resolucion?: string | null;
}

export interface RegistrarTramitePayload {
  readonly dni: string;
  readonly tipo_documento: TipoDocumento;
  readonly dependencia: string;
  readonly contenedor: string;
}

const DEFAULT_BASE_URL = "http://localhost:8000";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  DEFAULT_BASE_URL;

async function parseError(response: Response): Promise<ApiError> {
  let detail = `HTTP ${response.status}`;
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (body?.detail) detail = body.detail;
  } catch {
    // Cuerpo no JSON.
  }
  return new ApiError(response.status, detail);
}

export async function registrarTramite(
  payload: RegistrarTramitePayload,
): Promise<TramiteDb> {
  const response = await fetch(`${API_BASE_URL}/api/tramites/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) throw await parseError(response);

  return (await response.json()) as TramiteDb;
}


export interface ReemplazarTramitePayload {
  readonly dni: string;
  readonly contenedor: string;
}

export async function reemplazarTramite(
  tramiteId: number,
  payload: ReemplazarTramitePayload,
): Promise<TramiteDb> {
  const response = await fetch(`${API_BASE_URL}/api/tramites/${tramiteId}/reemplazo`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) throw await parseError(response);

  return (await response.json()) as TramiteDb;
}

export async function buscarTramites(params: {
  dni: string;
  tipo_documento: TipoDocumento;
  fecha_desde: string;
  fecha_hasta: string;
}): Promise<readonly TramiteDb[]> {
  const query = new URLSearchParams({
    tipo_documento: params.tipo_documento,
    fecha_desde: params.fecha_desde,
    fecha_hasta: params.fecha_hasta,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/tramites/${params.dni}/buscar?${query.toString()}`,
  );

  if (!response.ok) throw await parseError(response);

  return (await response.json()) as readonly TramiteDb[];
}
