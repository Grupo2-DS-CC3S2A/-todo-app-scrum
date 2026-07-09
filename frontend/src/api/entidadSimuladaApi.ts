export interface DocumentoEntidad {
  readonly id: number;
  readonly dependencia: string;
  readonly nro_documento: string;
  readonly estado_documento: string;
  readonly fecha_tramite: string;
  readonly fecha_respuesta: string;
  readonly contenedor: string;
}

export interface VerificacionFirmaResult {
  readonly tramite_id: number;
  readonly nro_documento: string;
  readonly verificacion_correcta: boolean;
  readonly mensaje: string;
  readonly detalle?: unknown;
}

export interface PaqueteDescargado {
  readonly filename: string;
  readonly blob: Blob;
}

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  DEFAULT_API_BASE_URL;

function buildUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

async function readError(response: Response): Promise<string> {
  const text = await response.text();

  if (!text) {
    return "No se pudo completar la operación.";
  }

  try {
    const json = JSON.parse(text) as { detail?: string };
    return json.detail || text;
  } catch {
    return text;
  }
}

// ``dependencia`` vacío/omitido solo tiene efecto para un admin (lista
// todas); el backend ignora el parámetro por completo si quien llama es
// operador y fuerza su propia ``dependencia_asignada``.
export async function listarDocumentosEntidad(
  dependencia: string | undefined,
  token: string,
): Promise<readonly DocumentoEntidad[]> {
  const query = dependencia ? `?${new URLSearchParams({ dependencia }).toString()}` : "";

  const response = await fetch(buildUrl(`/api/entidad-simulada/documentos${query}`), {
    headers: authHeaders(token),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as readonly DocumentoEntidad[];
}

export async function verificarFirmaEntidad(
  tramiteId: number,
  token: string,
): Promise<VerificacionFirmaResult> {
  const response = await fetch(
    buildUrl(`/api/entidad-simulada/documentos/${tramiteId}/verificar`),
    {
      method: "POST",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as VerificacionFirmaResult;
}

export async function borrarDocumentoEntidad(
  tramiteId: number,
  token: string,
): Promise<void> {
  const response = await fetch(
    buildUrl(`/api/entidad-simulada/documentos/${tramiteId}`),
    {
      method: "DELETE",
      headers: authHeaders(token),
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}

// El endpoint exige JWT, por lo que no puede navegarse con window.open():
// se descarga el blob autenticado y se dispara la descarga desde el cliente.
export async function descargarPaqueteEntidad(
  tramiteId: number,
  token: string,
): Promise<PaqueteDescargado> {
  const response = await fetch(
    buildUrl(`/api/entidad-simulada/documentos/${tramiteId}/download-paquete`),
    { headers: authHeaders(token) },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^"]+)"?/.exec(disposition);
  const filename = match?.[1] ?? `documento_${tramiteId}.zip`;

  return { filename, blob: await response.blob() };
}
