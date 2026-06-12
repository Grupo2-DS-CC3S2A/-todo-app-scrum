/**
 * Contexto y hook de autenticacion JWT (SCRUM-24 / S2-05).
 *
 * El proveedor del contexto vive en ``AuthProvider.tsx`` para poder usar JSX.
 * Este modulo exporta solo el contexto y el hook ``useAuth``.
 *
 * Uso:
 * ```tsx
 * // main.tsx — envuelve la app
 * <AuthProvider><App /></AuthProvider>
 *
 * // cualquier componente o hook hijo
 * const { sesion, isAutenticado, iniciarSesion, cerrarSesion } = useAuth();
 * ```
 */

import { createContext, useContext } from "react";
import { ApiError } from "@/types/voting";
import type { LoginInput, SesionActiva } from "@/types/auth";

export { ApiError };
export type { LoginInput, SesionActiva };

export interface UseAuthResult {
  readonly sesion: SesionActiva | null;
  readonly isAutenticado: boolean;
  readonly cargando: boolean;
  readonly error: ApiError | null;
  readonly iniciarSesion: (payload: LoginInput) => Promise<boolean>;
  readonly cerrarSesion: () => void;
}

export const AuthContext = createContext<UseAuthResult | null>(null);

export function useAuth(): UseAuthResult {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  }
  return ctx;
}
