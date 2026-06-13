import { ApiError, type ApiErrorBody } from "@/types/voting";
import type {
  CiudadanoValidado,
  ValidacionCiudadanoInput,
  ValidacionCiudadanoResponse,
} from "@/types/ciudadano";

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
    // Cuerpo no JSON.
  }
  return new ApiError(response.status, detail, tipo);
}

export async function validarCiudadano(
  payload: ValidacionCiudadanoInput,
): Promise<CiudadanoValidado | null> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor.", "NetworkError");
  }

  if (!response.ok) throw await parseError(response);
  const body = (await response.json()) as ValidacionCiudadanoResponse;
  if (!body.valid || !body.dni || !body.firstname || !body.lastname) return null;
  return {
    dni: body.dni,
    firstname: body.firstname,
    lastname: body.lastname,
  };
}
