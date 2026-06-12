/**
 * Vista de inicio de sesion (SCRUM-23 / HU01).
 *
 * Layout institucional RENIEC identico al de la aplicacion principal:
 * panel izquierdo con marca y tagline, panel derecho con el formulario
 * de credenciales. El estado asincrono (cargando / error) lo inyecta
 * ``useAuth`` sin que el componente acople logica de transporte.
 */

import { useState, type FormEvent, type ReactElement } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Image,
  Input,
  Stack,
  Text,
} from "@chakra-ui/react";

import { useAuth } from "@/hooks/useAuth";

export function LoginPage(): ReactElement {
  const { iniciarSesion, cargando, error } = useAuth();
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    void iniciarSesion({ username, password });
  };

  return (
    <Box minH="100vh" bg="gray.50" color="gray.800">
      {/* Barra superior institucional */}
      <Box bg="#1A3A6B" py={3} px={8}>
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
      </Box>

      {/* Contenido principal centrado */}
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
            <Text
              color="white"
              fontSize="xs"
              letterSpacing="widest"
              textTransform="uppercase"
            >
              Seguro · Anonimo · Trazable
            </Text>
          </Box>
        </Box>

        {/* Panel derecho — formulario de login */}
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
                Inicio de Sesion
              </Heading>
              <Text color="gray.500" fontSize="sm">
                Ingresa tus credenciales para acceder al sistema.
              </Text>
            </Stack>

            <form onSubmit={handleSubmit} noValidate>
              <Stack gap={4}>
                <Box>
                  <Text mb={2} color="gray.700" fontWeight="medium" fontSize="sm">
                    Usuario
                  </Text>
                  <Input
                    placeholder="Nombre de usuario"
                    autoComplete="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </Box>

                <Box>
                  <Text mb={2} color="gray.700" fontWeight="medium" fontSize="sm">
                    Contrasena
                  </Text>
                  <Input
                    type="password"
                    placeholder="Contrasena"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </Box>

                {error && (
                  <Box
                    bg="red.50"
                    border="1px solid"
                    borderColor="red.200"
                    borderRadius="md"
                    p={3}
                  >
                    <Text color="red.700" fontSize="sm">
                      {error.message}
                    </Text>
                  </Box>
                )}

                <Button
                  type="submit"
                  colorPalette="blue"
                  loading={cargando}
                  loadingText="Verificando credenciales"
                  w="full"
                >
                  Ingresar al Sistema
                </Button>
              </Stack>
            </form>

            <Text color="gray.400" fontSize="xs" textAlign="center" mt={2}>
              Sistema protegido bajo normas de la Ley N° 27269 — RENIEC 2026
            </Text>
          </Stack>
        </Box>
      </Flex>
    </Box>
  );
}
