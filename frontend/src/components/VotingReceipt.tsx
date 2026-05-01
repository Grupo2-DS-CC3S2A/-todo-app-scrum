/**
 * Comprobante visual del voto cifrado emitido.
 */

import type { ReactElement } from "react";
import { Card, Heading, Stack, Text } from "@chakra-ui/react";

import type { VotoCifrado } from "@/types/voting";

export interface VotingReceiptProps {
  readonly comprobante: VotoCifrado;
}

function formatTimestamp(epoch: number): string {
  return new Date(epoch * 1000).toISOString();
}

export function VotingReceipt({ comprobante }: VotingReceiptProps): ReactElement {
  return (
    <Card.Root bg="green.900" borderColor="green.700" p={5}>
      <Heading size="md" mb={3}>
        Voto Procesado Exitosamente
      </Heading>
      <Text fontSize="sm" color="gray.300">
        Tu voto ha sido cifrado y es anonimo.
      </Text>
      <Stack
        mt={3}
        p={3}
        bg="blackAlpha.500"
        rounded="md"
        fontSize="xs"
        fontFamily="monospace"
      >
        <Text wordBreak="break-all">
          <b>Hash Cifrado:</b> {comprobante.hash_voto}
        </Text>
        <Text>
          <b>Llave Genetica:</b> {comprobante.clave_genetica}
        </Text>
        <Text>
          <b>Timestamp:</b> {formatTimestamp(comprobante.timestamp)}
        </Text>
      </Stack>
    </Card.Root>
  );
}
