/**
 * Cabecera con titulo y descripcion del sistema de votacion.
 */

import type { ReactElement } from "react";
import { Heading, Stack, Text } from "@chakra-ui/react";

export function Header(): ReactElement {
  return (
    <Stack gap={2}>
      <Heading size="lg">Mesa de Partes Electronica</Heading>
      <Text color="gray.300">
        Emite tu voto de forma segura. Utilizamos cifrado SHA-256 y llaves
        evolutivas para garantizar anonimato e inmutabilidad.
      </Text>
    </Stack>
  );
}
