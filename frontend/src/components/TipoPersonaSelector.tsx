/**
 * Selector de tipo de persona al ingreso.
 * Se muestra antes del formulario de solicitud y condiciona si
 * se exigira DNI para Natural o RUC para Juridica, capturando el
 * numero de documento que valida DocumentoFactory (MDP-15) en el backend.
 */

import { useMemo, type ReactElement } from "react";
import { Box, Input, NativeSelect, Text } from "@chakra-ui/react";

import {
  CATALOGO_TIPO_PERSONA,
  TipoPersona,
  type TipoPersonaCatalogoItem,
} from "@/types/tipoPersona";

export interface TipoPersonaSelectorProps {
  readonly value: TipoPersona;
  readonly onChange: (tipoPersona: TipoPersona) => void;
  readonly numeroDocumento: string;
  readonly onNumeroDocumentoChange: (numeroDocumento: string) => void;
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
  numeroDocumento,
  onNumeroDocumentoChange,
  disabled = false,
}: TipoPersonaSelectorProps): ReactElement {
  const seleccionado = useMemo(() => buscarTipoPersona(value), [value]);

  const documentoValido =
    numeroDocumento.length === 0 ||
    seleccionado.documentoPattern.test(numeroDocumento);

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

      <Box mt={3}>
        <Text mb={2}>{seleccionado.documentoLabel}</Text>
        <Input
          value={numeroDocumento}
          onChange={(e) =>
            onNumeroDocumentoChange(e.currentTarget.value.replace(/\D/g, ""))
          }
          placeholder={`${seleccionado.documentoLabel} (${seleccionado.documentoLongitud} dígitos)`}
          maxLength={seleccionado.documentoLongitud}
          disabled={disabled}
          inputMode="numeric"
          borderColor={documentoValido ? undefined : "red.400"}
        />
        {!documentoValido && (
          <Text fontSize="xs" color="red.400" mt={1}>
            El {seleccionado.documentoLabel} debe tener{" "}
            {seleccionado.documentoLongitud} dígitos.
          </Text>
        )}
      </Box>
    </Box>
  );
}
