/**
 * Cliente HTTP del modulo de votacion.
 *
 * Centraliza la URL base, la serializacion JSON y el mapeo de errores hacia
 * la clase {@link ApiError} para que las capas superiores no tengan que
 * tratar con la API de ``fetch`` directamente.
 */

import { ApiError, type ApiErrorBody, type VotoCifrado, type VotoInput } from "@/types/voting";

const DEFAULT_BASE_URL = "http://localhost:8000";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || DEFAULT_BASE_URL;

async function parseError(response: Response): Promise<ApiError> {
  let detail = `HTTP ${response.status}`;
  let tipo: string | undefined;
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (body?.detail) detail = body.detail;
    tipo = body?.tipo;
  } catch {
    // Cuerpo no JSON; conservamos detalle por defecto.
  }
  return new ApiError(response.status, detail, tipo);
}

export async function emitirVoto(payload: VotoInput): Promise<VotoCifrado> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/votar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.", "NetworkError");
  }

  if (!response.ok) throw await parseError(response);
  return (await response.json()) as VotoCifrado;
}
