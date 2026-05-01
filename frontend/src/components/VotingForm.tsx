/**
 * Formulario controlado para la emision del voto.
 *
 * No conoce de fetch ni de estado global: recibe un callback ``onSubmit`` y
 * un flag ``cargando`` desde el hook ``useVoting``.
 */

import { useState, type FormEvent, type ReactElement } from "react";
import { Box, Button, Card, Input, Stack, Text } from "@chakra-ui/react";

import type { VotoInput } from "@/types/voting";

const DNI_PATTERN = /^\d{8}$/;

export interface VotingFormProps {
  readonly cargando: boolean;
  readonly onSubmit: (payload: VotoInput) => unknown;
  readonly onValidationError: (mensaje: string) => void;
}

export function VotingForm({
  cargando,
  onSubmit,
  onValidationError,
}: VotingFormProps): ReactElement {
  const [dni, setDni] = useState<string>("");
  const [candidatoId, setCandidatoId] = useState<string>("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!DNI_PATTERN.test(dni)) {
      onValidationError("El DNI debe tener exactamente 8 digitos.");
      return;
    }
    const idCandidato = Number.parseInt(candidatoId, 10);
    if (!Number.isInteger(idCandidato) || idCandidato < 1) {
      onValidationError("Selecciona un id de candidato valido (>= 1).");
      return;
    }
    void onSubmit({ dni_votante: dni, id_candidato: idCandidato });
  };

  return (
    <Card.Root bg="gray.800" borderColor="gray.700" p={5}>
      <form onSubmit={handleSubmit} noValidate>
        <Stack gap={4}>
          <Box>
            <Text mb={2}>DNI del Votante</Text>
            <Input
              placeholder="Ingresa tu DNI (8 digitos)"
              inputMode="numeric"
              maxLength={8}
              value={dni}
              onChange={(e) => setDni(e.target.value.replace(/\D/g, ""))}
              required
            />
          </Box>
          <Box>
            <Text mb={2}>ID de Candidato</Text>
            <Input
              placeholder="Ej. 1"
              type="number"
              min={1}
              value={candidatoId}
              onChange={(e) => setCandidatoId(e.target.value)}
              required
            />
          </Box>
          <Button
            type="submit"
            colorPalette="blue"
            loading={cargando}
            loadingText="Procesando voto"
          >
            Emitir Voto Seguro
          </Button>
        </Stack>
      </form>
    </Card.Root>
  );
}
