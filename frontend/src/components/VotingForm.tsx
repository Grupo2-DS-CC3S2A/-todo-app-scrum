import { useEffect, useState, type FormEvent, type ReactElement } from "react";

import type { VotoInput } from "@/types/voting";

const DNI_PATTERN = /^\d{8}$/;

export interface VotingFormProps {
  readonly cargando: boolean;
  readonly dniInicial?: string;
  readonly bloquearDni?: boolean;
  readonly onSubmit: (payload: VotoInput) => unknown;
  readonly onValidationError: (mensaje: string) => void;
}

export function VotingForm({
  cargando,
  dniInicial = "",
  bloquearDni = false,
  onSubmit,
  onValidationError,
}: VotingFormProps): ReactElement {
  const [dni, setDni] = useState<string>(dniInicial);
  const [candidatoId, setCandidatoId] = useState<string>("1");

  useEffect(() => {
    setDni(dniInicial);
  }, [dniInicial]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!DNI_PATTERN.test(dni)) {
      onValidationError("El DNI debe tener exactamente 8 digitos numericos.");
      return;
    }
    const idCandidato = Number.parseInt(candidatoId, 10);
    if (!Number.isInteger(idCandidato) || idCandidato < 1) {
      onValidationError("Selecciona un ID de candidato valido, mayor o igual que 1.");
      return;
    }
    void onSubmit({ dni_votante: dni, id_candidato: idCandidato });
  };

  return (
    <form className="voting-form" onSubmit={handleSubmit} noValidate>
      <div className="form-group">
        <label htmlFor="vote-dni">DNI del Votante</label>
        <input
          id="vote-dni"
          type="text"
          inputMode="numeric"
          maxLength={8}
          value={dni}
          readOnly={bloquearDni}
          onChange={(e) => setDni(e.target.value.replace(/\D/g, ""))}
          placeholder="Ingrese DNI"
          required
        />
        {bloquearDni && (
          <p className="field-help">DNI tomado de la validacion de ingreso.</p>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="candidate-id">ID de Candidato</label>
        <input
          id="candidate-id"
          type="number"
          min={1}
          value={candidatoId}
          onChange={(e) => setCandidatoId(e.target.value)}
          placeholder="Ej. 1"
          required
        />
      </div>

      <button className="btn btn-primary btn-full" type="submit" disabled={cargando}>
        {cargando ? "Procesando voto..." : "Emitir Voto Seguro"}
      </button>
    </form>
  );
}
