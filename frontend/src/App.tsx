/**
 * Componente raiz: controla el flujo de autenticacion y compone las vistas.
 *
 * Flujo de renderizado:
 * 1. Mientras ``useAuth`` restaura la sesion desde localStorage → spinner.
 * 2. Sin sesion activa → ``LoginPage``.
 * 3. Con sesion activa → layout principal con formulario de voto y, si el
 *    rol es ``admin``, panel de derivacion de solicitudes.
 */

import { useEffect, type ReactElement } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Image,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";

import { AdminDerivacionPanel } from "@/components/AdminDerivacionPanel";
import { LoginPage } from "@/components/LoginPage";
import { VotingForm } from "@/components/VotingForm";
import { VotingReceipt } from "@/components/VotingReceipt";
import { toaster } from "@/components/ui/toaster";
import { useAuth } from "@/hooks/useAuth";
import { useVoting } from "@/hooks/useVoting";

function VistaAutenticada(): ReactElement {
  const { sesion, cerrarSesion } = useAuth();
  const { comprobante, cargando, error, votar } = useVoting();
  const esAdmin = sesion?.usuario.rol === "admin";

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
    <Box minH="100vh" bg="gray.50" color="gray.800">
      {/* Barra superior institucional */}
      <Box bg="#1A3A6B" py={3} px={8}>
        <Flex align="center" justify="space-between">
          <Flex align="center" gap={3}>
            <Image src="/reniec_logo.png" alt="RENIEC" h="40px" />
            <Box>
              <Text color="white" fontWeight="bold" fontSize="sm" letterSpacing="wider">
                RENIEC
              </Text>
              <Text color="blue.200" fontSize="xs">
                Registro Nacional de Identificacion y Estado Civil
              </Text>
            </Box>
          </Flex>

          <Flex align="center" gap={4}>
            <Box textAlign="right">
              <Text color="white" fontSize="sm" fontWeight="medium">
                {sesion?.usuario.username}
              </Text>
              <Text color="blue.200" fontSize="xs" textTransform="capitalize">
                {sesion?.usuario.rol}
              </Text>
            </Box>
            <Button
              size="sm"
              variant="outline"
              colorPalette="whiteAlpha"
              color="white"
              borderColor="whiteAlpha.400"
              onClick={cerrarSesion}
              _hover={{ bg: "whiteAlpha.200" }}
            >
              Cerrar sesion
            </Button>
          </Flex>
        </Flex>
      </Box>

      {/* Contenido principal */}
      <Flex
        minH="calc(100vh - 64px)"
        align="center"
        justify="center"
        px={6}
        py={10}
        gap={0}
        maxW="1100px"
        mx="auto"
      >
        {/* Panel izquierdo — imagen + tagline */}
        <Box
          flex="1"
          display={{ base: "none", md: "flex" }}
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          bg="#1A3A6B"
          minH="520px"
          borderRadius="2xl 0 0 2xl"
          p={10}
          gap={6}
        >
          <Image
            src="/reniec_logo.png"
            alt="RENIEC logo"
            w="180px"
            filter="drop-shadow(0 4px 24px rgba(0,0,0,0.4))"
          />
          <Stack gap={3} textAlign="center">
            <Heading size="lg" color="white" fontWeight="extrabold">
              Mesa de Partes
            </Heading>
            <Heading size="md" color="blue.200" fontWeight="medium">
              Electronica RENIEC
            </Heading>
            <Text color="blue.100" fontSize="sm" maxW="260px" lineHeight="tall">
              Sistema de voto electronico seguro con cifrado SHA-256 y llaves
              evolutivas para garantizar anonimato e inmutabilidad.
            </Text>
          </Stack>
          <Box
            mt={4}
            px={4}
            py={2}
            bg="whiteAlpha.200"
            borderRadius="full"
            border="1px solid"
            borderColor="whiteAlpha.300"
          >
            <Text color="white" fontSize="xs" letterSpacing="widest" textTransform="uppercase">
              Seguro · Anonimo · Trazable
            </Text>
          </Box>
        </Box>

        {/* Panel derecho */}
        <Box
          flex="1"
          bg="white"
          borderRadius={{ base: "2xl", md: "0 2xl 2xl 0" }}
          boxShadow="2xl"
          p={{ base: 6, md: 10 }}
          minH="520px"
          display="flex"
          flexDirection="column"
          justifyContent="center"
        >
          <Stack gap={6}>
            <Stack gap={1}>
              <Heading size="md" color="#1A3A6B" fontWeight="bold">
                Registro de Solicitud
              </Heading>
              <Text color="gray.500" fontSize="sm">
                Ingresa tus datos para emitir tu voto de forma segura.
              </Text>
            </Stack>

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

            {esAdmin && (
              <Box mt={4}>
                <AdminDerivacionPanel />
              </Box>
            )}

            <Text color="gray.400" fontSize="xs" textAlign="center" mt={2}>
              Sistema protegido bajo normas de la Ley N° 27269 — RENIEC 2026
            </Text>
          </Stack>
        </Box>
      </Flex>
    </Box>
  );
}

export default function App(): ReactElement {
  const { isAutenticado, cargando } = useAuth();

  if (cargando) {
    return (
      <Flex minH="100vh" align="center" justify="center" bg="gray.50">
        <Spinner size="xl" color="#1A3A6B" />
      </Flex>
    );
  }

  if (!isAutenticado) {
    return <LoginPage />;
  }

  return <VistaAutenticada />;
}
