export interface DependenciaDb {
  readonly id: number;
  readonly nombre: string;
  readonly codigo_interno: string;
}

const DEFAULT_BASE_URL = "http://localhost:8000";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  DEFAULT_BASE_URL;

export async function listarDependencias(): Promise<readonly DependenciaDb[]> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/dependencias/`);
  } catch {
    throw new Error("No se pudo conectar con el servidor.");
  }

  if (!response.ok) {
    throw new Error("No se pudieron cargar las dependencias.");
  }

  return (await response.json()) as readonly DependenciaDb[];
}