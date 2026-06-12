/**
 * Proveedor del contexto de autenticacion JWT (SCRUM-24 / S2-05).
 *
 * Responsabilidades:
 * - Persistir el JWT en ``localStorage`` con su timestamp de expiracion.
 * - Restaurar la sesion al montar la aplicacion validando el token contra
 *   ``GET /api/auth/me`` (detecta tokens revocados o usuario eliminado).
 * - Exponer ``iniciarSesion`` y ``cerrarSesion`` al arbol de componentes.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";

import { obtenerPerfil, solicitarLogin } from "@/api/authApi";
import { AuthContext, type UseAuthResult } from "@/hooks/useAuth";
import { ApiError } from "@/types/voting";
import type { LoginInput, SesionActiva } from "@/types/auth";

const TOKEN_KEY = "reniec_token";
const EXPIRA_KEY = "reniec_token_expira";

function leerTokenGuardado(): { token: string; expiraEn: number } | null {
  const token = localStorage.getItem(TOKEN_KEY);
  const expiraStr = localStorage.getItem(EXPIRA_KEY);
  if (!token || !expiraStr) return null;
  const expiraEn = Number(expiraStr);
  if (Date.now() >= expiraEn) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EXPIRA_KEY);
    return null;
  }
  return { token, expiraEn };
}

function limpiarStorage(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EXPIRA_KEY);
}

export function AuthProvider({
  children,
}: {
  readonly children: ReactNode;
}): ReactElement {
  const [sesion, setSesion] = useState<SesionActiva | null>(null);
  const [cargando, setCargando] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);

  // Restaurar sesion previa desde localStorage al montar la aplicacion.
  useEffect(() => {
    async function restaurar(): Promise<void> {
      const guardado = leerTokenGuardado();
      if (!guardado) {
        setCargando(false);
        return;
      }
      try {
        const usuario = await obtenerPerfil(guardado.token);
        setSesion({ token: guardado.token, usuario, expiraEn: guardado.expiraEn });
      } catch {
        // Token invalido o usuario eliminado: descartar sesion guardada.
        limpiarStorage();
      } finally {
        setCargando(false);
      }
    }
    void restaurar();
  }, []);

  const iniciarSesion = useCallback(
    async (payload: LoginInput): Promise<boolean> => {
      setCargando(true);
      setError(null);
      try {
        const respToken = await solicitarLogin(payload);
        const expiraEn = Date.now() + respToken.expires_in * 1000;
        const usuario = await obtenerPerfil(respToken.access_token);
        localStorage.setItem(TOKEN_KEY, respToken.access_token);
        localStorage.setItem(EXPIRA_KEY, String(expiraEn));
        setSesion({ token: respToken.access_token, usuario, expiraEn });
        return true;
      } catch (err) {
        const apiErr =
          err instanceof ApiError
            ? err
            : new ApiError(0, "Error inesperado al iniciar sesion.");
        setError(apiErr);
        return false;
      } finally {
        setCargando(false);
      }
    },
    [],
  );

  const cerrarSesion = useCallback((): void => {
    limpiarStorage();
    setSesion(null);
    setError(null);
  }, []);

  const valor = useMemo<UseAuthResult>(
    () => ({
      sesion,
      isAutenticado: sesion !== null,
      cargando,
      error,
      iniciarSesion,
      cerrarSesion,
    }),
    [sesion, cargando, error, iniciarSesion, cerrarSesion],
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}
