/**
 * Cliente HTTP del modulo de autenticacion (HU01 / S2-05).
 *
 * Cubre los endpoints:
 * - ``POST /api/auth/login`` → emite JWT
 * - ``GET  /api/auth/me``    → devuelve el perfil del usuario autenticado
 */

import { ApiError, type ApiErrorBody } from "@/types/voting";
import type { LoginInput, TokenResponse, UsuarioPublico } from "@/types/auth";

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

export async function solicitarLogin(
  payload: LoginInput,
): Promise<TokenResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.", "NetworkError");
  }
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as TokenResponse;
}

export async function obtenerPerfil(token: string): Promise<UsuarioPublico> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.", "NetworkError");
  }
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as UsuarioPublico;
}
