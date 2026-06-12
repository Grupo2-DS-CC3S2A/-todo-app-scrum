/**
 * Cliente HTTP del modulo Mesa de Partes (HU04).
 *
 * Aisla a las capas superiores del transporte ``fetch`` y unifica el
 * tratamiento de errores via {@link ApiError}.
 *
 * Los endpoints de admin aceptan ``Authorization: Bearer <token>`` (S2-05).
 * El esquema ``X-Admin-Token`` sigue siendo aceptado por el backend pero
 * este cliente ya no lo emite (SCRUM-24).
 */

import { ApiError, type ApiErrorBody } from "@/types/voting";
import type { DerivacionInput, Solicitud } from "@/types/derivacion";

const DEFAULT_BASE_URL = "http://localhost:8000";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  DEFAULT_BASE_URL;

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

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      ...init,
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.", "NetworkError");
  }
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export function listarSolicitudesEntrantes(
  token: string,
): Promise<readonly Solicitud[]> {
  return request<readonly Solicitud[]>("/api/admin/solicitudes", token);
}

export function derivarSolicitud(
  _idSolicitud: number,
  payload: DerivacionInput,
  token: string,
): Promise<Solicitud> {
  return request<Solicitud>("/api/admin/solicitudes/derivar", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
