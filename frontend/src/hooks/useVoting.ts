/**
 * Custom Hook que encapsula el ciclo de vida de la emision de un voto.
 *
 * Maneja loading, error, comprobante y resetea el estado, exponiendo una
 * API minima al componente consumidor (SRP).
 */

import { useCallback, useState } from "react";

import { emitirVoto } from "@/api/votingApi";
import { ApiError, type VotoCifrado, type VotoInput } from "@/types/voting";

export interface UseVotingState {
  readonly comprobante: VotoCifrado | null;
  readonly cargando: boolean;
  readonly error: ApiError | null;
}

export interface UseVotingResult extends UseVotingState {
  readonly votar: (payload: VotoInput) => Promise<VotoCifrado | null>;
  readonly reset: () => void;
}

const ESTADO_INICIAL: UseVotingState = {
  comprobante: null,
  cargando: false,
  error: null,
};

export function useVoting(): UseVotingResult {
  const [estado, setEstado] = useState<UseVotingState>(ESTADO_INICIAL);

  const votar = useCallback(
    async (payload: VotoInput): Promise<VotoCifrado | null> => {
      setEstado({ comprobante: null, cargando: true, error: null });
      try {
        const comprobante = await emitirVoto(payload);
        setEstado({ comprobante, cargando: false, error: null });
        return comprobante;
      } catch (err) {
        const error =
          err instanceof ApiError
            ? err
            : new ApiError(0, "Error inesperado en el cliente.");
        setEstado({ comprobante: null, cargando: false, error });
        return null;
      }
    },
    [],
  );

  const reset = useCallback((): void => {
    setEstado(ESTADO_INICIAL);
  }, []);

  return { ...estado, votar, reset };
}
