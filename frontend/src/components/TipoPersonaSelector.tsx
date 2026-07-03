/**
 * Selector de tipo de persona al ingreso.
 * Se muestra antes del formulario de solicitud y condiciona si
 * se exigira DNI para Natural o RUC para Juridica
 */

import { useMemo, type ReactElement } from "react";
import { Box, NativeSelect, Text } from "@chakra-ui/react";

import {
  CATALOGO_TIPO_PERSONA,
  TipoPersona,
  type TipoPersonaCatalogoItem,
} from "@/types/tipoPersona";

export interface TipoPersonaSelectorProps {
  readonly value: TipoPersona;
  readonly onChange: (tipoPersona: TipoPersona) => void;
  readonly disabled?: boolean;
}

function buscarTipoPersona(codigo: TipoPersona): TipoPersonaCatalogoItem {
  const item = CATALOGO_TIPO_PERSONA.find((t) => t.codigo === codigo);
  if (!item) {
    throw new Error(`Tipo de persona desconocido: ${codigo}`);
  }
  return item;
}

export function TipoPersonaSelector({
  value,
  onChange,
  disabled = false,
}: TipoPersonaSelectorProps): ReactElement {
  const seleccionado = useMemo(() => buscarTipoPersona(value), [value]);

  return (
    <Box>
      <Text mb={2}>Tipo de Persona</Text>
      <NativeSelect.Root size="md" disabled={disabled}>
        <NativeSelect.Field
          value={value}
          onChange={(e) => onChange(e.currentTarget.value as TipoPersona)}
        >
          {CATALOGO_TIPO_PERSONA.map((t) => (
            <option key={t.codigo} value={t.codigo}>
              {t.etiqueta}
            </option>
          ))}
        </NativeSelect.Field>
        <NativeSelect.Indicator />
      </NativeSelect.Root>
      <Text fontSize="xs" color="gray.500" mt={1}>
        Documento requerido: {seleccionado.documentoLabel} (
        {seleccionado.documentoLongitud} dígitos).
      </Text>
    </Box>
  );
}
