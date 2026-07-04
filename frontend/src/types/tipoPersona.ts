/**
 * Tipo de persona solicitante.
 * Espeja el enum Pydantic `TipoPersona` del backend
 * `backend/src/modelos/tipo_persona.py`, cuyos valores en mayúsculas
 * coinciden con el tipo `tipo_persona` definido.
 */

export const TipoPersona = {
  NATURAL: "NATURAL",
  JURIDICA: "JURIDICA",
} as const;

export type TipoPersona = (typeof TipoPersona)[keyof typeof TipoPersona];

export interface TipoPersonaCatalogoItem {
  readonly codigo: TipoPersona;
  readonly etiqueta: string;
  readonly documentoLabel: string;
  readonly documentoLongitud: number;
  readonly documentoPattern: RegExp;
}

export const CATALOGO_TIPO_PERSONA: readonly TipoPersonaCatalogoItem[] = [
  {
    codigo: TipoPersona.NATURAL,
    etiqueta: "Persona Natural",
    documentoLabel: "DNI",
    documentoLongitud: 8,
    documentoPattern: /^\d{8}$/,
  },
  {
    codigo: TipoPersona.JURIDICA,
    etiqueta: "Persona Jurídica",
    documentoLabel: "RUC",
    documentoLongitud: 11,
    documentoPattern: /^\d{11}$/,
  },
];
