/**
 * Custom Hook que encapsula el flujo asincrono de la HU04.
 *
 * Lista solicitudes entrantes y ejecuta la derivacion contra el backend,
 * exponiendo loading/error/data al componente sin acoplarlo a ``fetch``
 * (Single Responsibility Principle).
 *
 * SCRUM-24: el JWT se obtiene de ``useAuth`` y se inyecta en cada llamada
 * al API. Las peticiones se suspenden si no hay sesion activa.
 */

import { useCallback, useEffect, useState } from "react";

import {
  derivarSolicitud,
  listarSolicitudesEntrantes,
} from "@/api/derivacionApi";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/types/voting";
import type { DerivacionInput, Solicitud } from "@/types/derivacion";

export interface UseDerivacionState {
  readonly solicitudes: readonly Solicitud[];
  readonly cargandoListado: boolean;
  readonly enviandoDerivacion: boolean;
  readonly errorListado: ApiError | null;
  readonly errorDerivacion: ApiError | null;
  readonly ultimaDerivada: Solicitud | null;
}

export interface UseDerivacionResult extends UseDerivacionState {
  readonly recargar: () => Promise<void>;
  readonly derivar: (
    idSolicitud: number,
    payload: DerivacionInput,
  ) => Promise<Solicitud | null>;
  readonly limpiarUltima: () => void;
}

const ESTADO_INICIAL: UseDerivacionState = {
  solicitudes: [],
  cargandoListado: false,
  enviandoDerivacion: false,
  errorListado: null,
  errorDerivacion: null,
  ultimaDerivada: null,
};

function aApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  return new ApiError(0, "Error inesperado en el cliente.");
}

export function useDerivacion(): UseDerivacionResult {
  const { sesion } = useAuth();
  const [estado, setEstado] = useState<UseDerivacionState>(ESTADO_INICIAL);

  const recargar = useCallback(async (): Promise<void> => {
    if (!sesion) return;
    setEstado((prev) => ({ ...prev, cargandoListado: true, errorListado: null }));
    try {
      const solicitudes = await listarSolicitudesEntrantes(sesion.token);
      setEstado((prev) => ({
        ...prev,
        solicitudes,
        cargandoListado: false,
      }));
    } catch (err) {
      setEstado((prev) => ({
        ...prev,
        cargandoListado: false,
        errorListado: aApiError(err),
      }));
    }
  }, [sesion]);

  const derivar = useCallback(
    async (
      idSolicitud: number,
      payload: DerivacionInput,
    ): Promise<Solicitud | null> => {
      if (!sesion) {
        setEstado((prev) => ({
          ...prev,
          errorDerivacion: new ApiError(401, "Se requiere autenticacion."),
        }));
        return null;
      }
      setEstado((prev) => ({
        ...prev,
        enviandoDerivacion: true,
        errorDerivacion: null,
        ultimaDerivada: null,
      }));
      try {
        const derivada = await derivarSolicitud(idSolicitud, payload, sesion.token);
        setEstado((prev) => ({
          ...prev,
          enviandoDerivacion: false,
          ultimaDerivada: derivada,
          solicitudes: prev.solicitudes.filter((s) => s.id !== derivada.id),
        }));
        return derivada;
      } catch (err) {
        setEstado((prev) => ({
          ...prev,
          enviandoDerivacion: false,
          errorDerivacion: aApiError(err),
        }));
        return null;
      }
    },
    [sesion],
  );

  const limpiarUltima = useCallback((): void => {
    setEstado((prev) => ({ ...prev, ultimaDerivada: null }));
  }, []);

  // Carga el listado cuando la sesion queda disponible.
  useEffect(() => {
    void recargar();
  }, [recargar]);

  return { ...estado, recargar, derivar, limpiarUltima };
}
