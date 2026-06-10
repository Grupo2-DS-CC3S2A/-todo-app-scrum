export interface ValidacionCiudadanoInput {
  readonly dni: string;
  readonly digit: string;
  readonly date: string;
}

export interface CiudadanoValidado {
  readonly dni: string;
  readonly firstname: string;
  readonly lastname: string;
}

export interface ValidacionCiudadanoResponse {
  readonly valid: boolean;
  readonly dni?: string | null;
  readonly firstname?: string | null;
  readonly lastname?: string | null;
}
