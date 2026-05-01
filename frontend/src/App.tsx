/**
 * Componente raiz: compone Header, formulario y comprobante.
 *
 * No contiene logica de fetch ni estado de red: delega en ``useVoting`` y
 * notifica al usuario via Chakra Toaster.
 */

import { useEffect, type ReactElement } from "react";
import { Box, Stack } from "@chakra-ui/react";

import { Header } from "@/components/Header";
import { VotingForm } from "@/components/VotingForm";
import { VotingReceipt } from "@/components/VotingReceipt";
import { toaster } from "@/components/ui/toaster";
import { useVoting } from "@/hooks/useVoting";

export default function App(): ReactElement {
  const { comprobante, cargando, error, votar } = useVoting();

  useEffect(() => {
    if (error) {
      toaster.create({
        type: "error",
        title: "No se pudo registrar el voto",
        description: error.message,
      });
    }
  }, [error]);

  useEffect(() => {
    if (comprobante) {
      toaster.create({
        type: "success",
        title: "Voto registrado",
        description: "Tu voto ha sido cifrado y almacenado de forma anonima.",
      });
    }
  }, [comprobante]);

  return (
    <Box minH="100vh" bg="gray.900" color="white" py={10} px={5}>
      <Stack maxW="xl" mx="auto" gap={6}>
        <Header />
        <VotingForm
          cargando={cargando}
          onSubmit={votar}
          onValidationError={(mensaje: string) =>
            toaster.create({
              type: "warning",
              title: "Datos invalidos",
              description: mensaje,
            })
          }
        />
        {comprobante && <VotingReceipt comprobante={comprobante} />}
      </Stack>
    </Box>
  );
}
