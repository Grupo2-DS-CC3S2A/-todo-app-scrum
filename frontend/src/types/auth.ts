/**
 * Tipos del dominio de autenticacion (HU01 / S2-05).
 *
 * Espejean 1:1 los modelos Pydantic del backend para evitar drift:
 * - ``LoginInput``     ← ``src/modelos/usuario.py::LoginInput``
 * - ``TokenResponse``  ← ``src/modelos/usuario.py::TokenResponse``
 * - ``UsuarioPublico`` ← ``src/modelos/usuario.py::UsuarioPublico``
 */

export type RolUsuario = "admin" | "operador" | "ciudadano";

export interface LoginInput {
  readonly username: string;
  readonly password: string;
}

export interface RegistroInput {
  readonly username: string;
  readonly password: string;
  readonly rol?: RolUsuario;
}

export interface TokenResponse {
  readonly access_token: string;
  readonly token_type: string;
  readonly expires_in: number;
}

export interface UsuarioPublico {
  readonly id: string;
  readonly username: string;
  readonly rol: RolUsuario;
  readonly created_at: string;
}

export interface SesionActiva {
  readonly token: string;
  readonly usuario: UsuarioPublico;
  readonly expiraEn: number; // timestamp en ms (Date.now())
}
