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

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "No se pudo registrar el trámite.");
  }

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

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "No se pudo consultar la búsqueda.");
  }

  return (await response.json()) as readonly TramiteDb[];
}
