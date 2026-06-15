/**
 * Custom Hook que encapsula el ciclo de vida de la emision de un voto.
 *
 * Maneja loading, error, comprobante y resetea el estado, exponiendo una
 * API minima al componente consumidor (SRP).
 */

import { useCallback, useState } from "react";

export interface UseVotingState {
  readonly comprobante: null;
  readonly cargando: boolean;
  readonly error: null;
}

export interface UseVotingResult extends UseVotingState {
  readonly reset: () => void;
}

const ESTADO_INICIAL: UseVotingState = {
  comprobante: null,
  cargando: false,
  error: null,
};

export function useVoting(): UseVotingResult {
  const [estado, setEstado] = useState<UseVotingState>(ESTADO_INICIAL);

  const reset = useCallback((): void => {
    setEstado(ESTADO_INICIAL);
  }, []);

  return { ...estado, reset };
}
