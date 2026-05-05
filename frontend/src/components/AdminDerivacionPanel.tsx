/**
 * Panel del administrador para derivar solicitudes entrantes (HU04).
 *
 * Solo se ocupa de la presentacion: el ciclo asincrono vive en
 * ``useDerivacion`` y la notificacion de exito/error se delega al
 * ``toaster`` global. Los calculos puros (fecha maxima, formato) se
 * extraen como helpers para mantener el componente declarativo.
 */

import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type ReactElement,
} from "react";
import {
  Badge,
  Box,
  Button,
  Card,
  Heading,
  HStack,
  NativeSelect,
  Stack,
  Text,
  Textarea,
} from "@chakra-ui/react";

import { toaster } from "@/components/ui/toaster";
import { useDerivacion } from "@/hooks/useDerivacion";
import {
  CATALOGO_DEPENDENCIAS,
  Dependencia,
  type DependenciaCatalogoItem,
  type Solicitud,
} from "@/types/derivacion";

const SIN_SELECCION = "" as const;

function esFinDeSemana(fecha: Date): boolean {
  const dia = fecha.getDay();
  return dia === 0 || dia === 6;
}

function calcularFechaMaxima(plazoDiasHabiles: number): Date {
  const fecha = new Date();
  let restantes = plazoDiasHabiles;
  while (restantes > 0) {
    fecha.setDate(fecha.getDate() + 1);
    if (!esFinDeSemana(fecha)) restantes -= 1;
  }
  return fecha;
}

function formatearFechaLarga(fecha: Date): string {
  return fecha.toLocaleDateString("es-PE", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function buscarDependencia(
  codigo: string,
): DependenciaCatalogoItem | undefined {
  return CATALOGO_DEPENDENCIAS.find((d) => d.codigo === codigo);
}

export function AdminDerivacionPanel(): ReactElement {
  const {
    solicitudes,
    cargandoListado,
    enviandoDerivacion,
    errorListado,
    errorDerivacion,
    ultimaDerivada,
    derivar,
    limpiarUltima,
  } = useDerivacion();

  const [idSolicitud, setIdSolicitud] = useState<string>(SIN_SELECCION);
  const [codigoDependencia, setCodigoDependencia] =
    useState<string>(SIN_SELECCION);
  const [observaciones, setObservaciones] = useState<string>("");

  const dependenciaSeleccionada = useMemo(
    () => buscarDependencia(codigoDependencia),
    [codigoDependencia],
  );

  const fechaMaximaPreview = useMemo(() => {
    if (!dependenciaSeleccionada) return null;
    return calcularFechaMaxima(dependenciaSeleccionada.plazo_dias_habiles);
  }, [dependenciaSeleccionada]);

  useEffect(() => {
    if (errorListado) {
      toaster.create({
        type: "error",
        title: "No se pudieron cargar las solicitudes",
        description: errorListado.message,
      });
    }
  }, [errorListado]);

  useEffect(() => {
    if (errorDerivacion) {
      toaster.create({
        type: "error",
        title: "Fallo el registro de la derivacion",
        description: errorDerivacion.message,
      });
    }
  }, [errorDerivacion]);

  useEffect(() => {
    if (!ultimaDerivada) return;
    toaster.create({
      type: "success",
      title: "Derivacion registrada",
      description: `Solicitud #${ultimaDerivada.id} ingresada en ${ultimaDerivada.dependencia ?? ""}.`,
    });
    setIdSolicitud(SIN_SELECCION);
    setCodigoDependencia(SIN_SELECCION);
    setObservaciones("");
    limpiarUltima();
  }, [ultimaDerivada, limpiarUltima]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const id = Number.parseInt(idSolicitud, 10);
    if (!Number.isInteger(id) || id < 1) {
      toaster.create({
        type: "warning",
        title: "Datos invalidos",
        description: "Selecciona una solicitud entrante.",
      });
      return;
    }
    if (!dependenciaSeleccionada) {
      toaster.create({
        type: "warning",
        title: "Datos invalidos",
        description: "Selecciona una dependencia destino.",
      });
      return;
    }
    void derivar(id, {
      dependencia: dependenciaSeleccionada.codigo as Dependencia,
      observaciones: observaciones.trim(),
    });
  };

  const sinSolicitudes = !cargandoListado && solicitudes.length === 0;

  return (
    <Card.Root bg="gray.800" borderColor="gray.700" p={5}>
      <Stack gap={4}>
        <HStack justify="space-between" align="center">
          <Heading size="md">Derivacion de Solicitudes (HU04)</Heading>
          <Badge colorPalette="yellow" variant="solid">
            Estado destino: Pendiente
          </Badge>
        </HStack>

        <form onSubmit={handleSubmit} noValidate>
          <Stack gap={4}>
            <Box>
              <Text mb={2}>Solicitud Entrante</Text>
              <NativeSelect.Root size="md" disabled={cargandoListado}>
                <NativeSelect.Field
                  value={idSolicitud}
                  onChange={(e) => setIdSolicitud(e.currentTarget.value)}
                >
                  <option value={SIN_SELECCION}>
                    {cargandoListado
                      ? "Cargando solicitudes..."
                      : sinSolicitudes
                        ? "No hay solicitudes registradas"
                        : "Selecciona una solicitud"}
                  </option>
                  {solicitudes.map((s: Solicitud) => (
                    <option key={s.id} value={String(s.id)}>
                      #{s.id} - {s.asunto} (DNI {s.dni_solicitante})
                    </option>
                  ))}
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

            <Box>
              <Text mb={2}>Dependencia Destino</Text>
              <NativeSelect.Root size="md">
                <NativeSelect.Field
                  value={codigoDependencia}
                  onChange={(e) => setCodigoDependencia(e.currentTarget.value)}
                >
                  <option value={SIN_SELECCION}>Selecciona una dependencia</option>
                  {CATALOGO_DEPENDENCIAS.map((d) => (
                    <option key={d.codigo} value={d.codigo}>
                      {d.etiqueta} ({d.plazo_dias_habiles} dias habiles)
                    </option>
                  ))}
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

            <Box bg="gray.900" borderWidth="1px" borderColor="gray.700" p={4} rounded="md">
              <Text fontSize="sm" color="gray.400" mb={1}>
                Fecha Maxima de Respuesta (preview)
              </Text>
              <Text fontWeight="semibold">
                {fechaMaximaPreview
                  ? formatearFechaLarga(fechaMaximaPreview)
                  : "Selecciona una dependencia para calcular el plazo"}
              </Text>
              {dependenciaSeleccionada && (
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Plazo de {dependenciaSeleccionada.plazo_dias_habiles} dias habiles
                  desde hoy.
                </Text>
              )}
            </Box>

            <Box>
              <Text mb={2}>Observaciones (opcional)</Text>
              <Textarea
                placeholder="Indicaciones para la dependencia destino"
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                maxLength={500}
                rows={3}
              />
            </Box>

            <Button
              type="submit"
              colorPalette="blue"
              loading={enviandoDerivacion}
              loadingText="Registrando derivacion"
              disabled={cargandoListado || sinSolicitudes}
            >
              Derivar Solicitud
            </Button>
          </Stack>
        </form>
      </Stack>
    </Card.Root>
  );
}
