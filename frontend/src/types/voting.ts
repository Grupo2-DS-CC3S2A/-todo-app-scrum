/**
 * Tipos del dominio de votacion compartidos por la UI y el cliente HTTP.
 *
 * Coinciden 1:1 con los modelos Pydantic del backend para evitar drift.
 */

export interface ApiErrorBody {
  readonly detail: string;
  readonly tipo?: string;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly tipo: string | undefined;

  constructor(status: number, message: string, tipo?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.tipo = tipo;
  }
}
