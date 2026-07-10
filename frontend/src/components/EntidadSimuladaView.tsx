import { useEffect, useMemo, useState } from "react";

import { listarDependencias, type DependenciaDb } from "../api/dependenciasApi";
import {
  borrarDocumentoEntidad,
  descargarPaqueteEntidad,
  listarDocumentosEntidad,
  resolverDocumentoEntidad,
  verificarFirmaEntidad,
  type DocumentoEntidad,
} from "../api/entidadSimuladaApi";
import type { UsuarioPublico } from "../types/auth";

import "../stylesEntidadSimulada.css";

interface EntidadSimuladaViewProps {
  readonly usuario: UsuarioPublico;
  readonly token: string;
  readonly onCerrarSesion: () => void;
}

export function EntidadSimuladaView({
  usuario,
  token,
  onCerrarSesion,
}: EntidadSimuladaViewProps): JSX.Element {
  const esOperador = usuario.rol === "operador";

  const [dependencias, setDependencias] = useState<readonly DependenciaDb[]>([]);
  const [dependenciaSeleccionada, setDependenciaSeleccionada] = useState("");
  const [documentos, setDocumentos] = useState<readonly DocumentoEntidad[]>([]);
  const [documentoSeleccionadoId, setDocumentoSeleccionadoId] = useState<number | null>(
    null,
  );
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mostrarFormularioRechazo, setMostrarFormularioRechazo] = useState(false);
  const [motivoRechazo, setMotivoRechazo] = useState("");

  const documentoSeleccionado = useMemo(
    () => documentos.find((documento) => documento.id === documentoSeleccionadoId) ?? null,
    [documentos, documentoSeleccionadoId],
  );

  const puedeResolver =
    !!documentoSeleccionado &&
    !cargando &&
    documentoSeleccionado.estado_documento === "EN TRAMITE";

  useEffect(() => {
    setMostrarFormularioRechazo(false);
    setMotivoRechazo("");
  }, [documentoSeleccionadoId]);

  async function cargarDocumentos(dependencia: string | undefined): Promise<void> {
    setCargando(true);
    setMensaje(null);
    setError(null);
    setDocumentoSeleccionadoId(null);

    try {
      // Un operador queda acotado a su propia dependencia del lado del
      // backend sin importar lo que se envíe aquí; el valor solo importa
      // para el filtro que puede elegir un admin.
      const data = await listarDocumentosEntidad(dependencia, token);
      setDocumentos(data);
    } catch (err) {
      setDocumentos([]);
      setError(err instanceof Error ? err.message : "No se pudieron cargar los documentos.");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    if (esOperador) {
      // Un operador no elige dependencia: revisa solo la que el admin le asignó.
      void cargarDocumentos(usuario.dependencia_asignada ?? undefined);
      return;
    }

    let mounted = true;

    async function cargarDependencias(): Promise<void> {
      try {
        const data = await listarDependencias();
        if (mounted) setDependencias(data);
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "No se pudieron cargar las dependencias.");
        }
      }
    }

    void cargarDependencias();

    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [esOperador]);

  if (esOperador && !usuario.dependencia_asignada) {
    return (
      <main className="entidad-page">
        <section className="entidad-card">
          <div className="entidad-message entidad-message-error">
            Su cuenta de operador no tiene una dependencia asignada. Contacte al
            administrador para poder revisar documentos.
          </div>
          <div className="flex-end mt-20">
            <button type="button" className="btn btn-secondary" onClick={onCerrarSesion}>
              Cerrar sesion
            </button>
          </div>
        </section>
      </main>
    );
  }

  async function handleDependenciaChange(
    event: React.ChangeEvent<HTMLSelectElement>,
  ): Promise<void> {
    const dependencia = event.target.value;
    setDependenciaSeleccionada(dependencia);
    await cargarDocumentos(dependencia || undefined);
  }

  async function handleVerificarFirma(): Promise<void> {
    if (!documentoSeleccionado) {
      return;
    }

    setCargando(true);
    setMensaje(null);
    setError(null);

    try {
      const result = await verificarFirmaEntidad(documentoSeleccionado.id, token);

      setMensaje(
        result.verificacion_correcta
          ? `Verificación correcta para el documento ${result.nro_documento}.`
          : `La verificación no fue satisfactoria para el documento ${result.nro_documento}.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo verificar la firma.");
    } finally {
      setCargando(false);
    }
  }

  async function handleDescargarDocumento(): Promise<void> {
    if (!documentoSeleccionado) {
      return;
    }

    setCargando(true);
    setMensaje(null);
    setError(null);

    try {
      const { filename, blob } = await descargarPaqueteEntidad(
        documentoSeleccionado.id,
        token,
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo descargar el documento.");
    } finally {
      setCargando(false);
    }
  }

  async function handleBorrarDocumento(): Promise<void> {
    if (!documentoSeleccionado) {
      return;
    }

    const confirmed = window.confirm(
      `¿Deseas borrar el documento ${documentoSeleccionado.nro_documento}?`,
    );

    if (!confirmed) {
      return;
    }

    setCargando(true);
    setMensaje(null);
    setError(null);

    try {
      await borrarDocumentoEntidad(documentoSeleccionado.id, token);

      setDocumentos((current) =>
        current.filter((documento) => documento.id !== documentoSeleccionado.id),
      );
      setDocumentoSeleccionadoId(null);
      setMensaje("Documento borrado correctamente.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo borrar el documento.");
    } finally {
      setCargando(false);
    }
  }

  async function handleAceptarDocumento(): Promise<void> {
    if (!documentoSeleccionado) {
      return;
    }

    setCargando(true);
    setMensaje(null);
    setError(null);

    try {
      const actualizado = await resolverDocumentoEntidad(
        documentoSeleccionado.id,
        "ACEPTADO",
        null,
        token,
      );
      setDocumentos((current) =>
        current.map((documento) => (documento.id === actualizado.id ? actualizado : documento)),
      );
      setMensaje(`Documento ${actualizado.nro_documento} aceptado.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo aceptar el documento.");
    } finally {
      setCargando(false);
    }
  }

  async function handleRechazarDocumento(): Promise<void> {
    if (!documentoSeleccionado) {
      return;
    }

    if (!motivoRechazo.trim()) {
      setError("Debe indicar un motivo para rechazar el documento.");
      return;
    }

    setCargando(true);
    setMensaje(null);
    setError(null);

    try {
      const actualizado = await resolverDocumentoEntidad(
        documentoSeleccionado.id,
        "RECHAZADO",
        motivoRechazo.trim(),
        token,
      );
      setDocumentos((current) =>
        current.map((documento) => (documento.id === actualizado.id ? actualizado : documento)),
      );
      setMensaje(`Documento ${actualizado.nro_documento} rechazado.`);
      setMostrarFormularioRechazo(false);
      setMotivoRechazo("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo rechazar el documento.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <main className="entidad-page">
      <section className="entidad-card">
        <div className="entidad-header-bar">
          <span className="entidad-usuario-info">
            {usuario.username} ({usuario.rol})
          </span>
          <button type="button" className="btn btn-secondary" onClick={onCerrarSesion}>
            Cerrar sesion
          </button>
        </div>

        <div className="entidad-review-box">
          {esOperador ? (
            <p className="entidad-label">
              Dependencia asignada: <strong>{usuario.dependencia_asignada}</strong>
            </p>
          ) : (
            <>
              <label className="entidad-label" htmlFor="dependencia-revisora">
                Dependencia Revisora
              </label>

              <select
                id="dependencia-revisora"
                value={dependenciaSeleccionada}
                onChange={(event) => void handleDependenciaChange(event)}
                className="entidad-select"
              >
                <option value="">Todas las dependencias</option>
                {dependencias.map((dependencia) => (
                  <option key={dependencia.id} value={dependencia.nombre}>
                    {dependencia.nombre}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>

        <div className="entidad-search-title">
          <h2>Busqueda de documentos tramitados</h2>
          <p>visualizar documentos tramitados.</p>
        </div>

        <div className="entidad-table-wrapper">
          <table className="entidad-table">
            <thead>
              <tr>
                <th>Dependencia</th>
                <th>Nro de Documento</th>
                <th>Estado Documento</th>
                <th>Fecha Tramite</th>
                <th>Fecha Respuesta</th>
              </tr>
            </thead>

            <tbody>
              {documentos.length === 0 ? (
                <tr>
                  <td className="entidad-empty" colSpan={5}>
                    {cargando
                      ? "Cargando documentos..."
                      : "No hay documentos tramitados para mostrar."}
                  </td>
                </tr>
              ) : (
                documentos.map((documento) => (
                  <tr
                    key={documento.id}
                    className={
                      documento.id === documentoSeleccionadoId
                        ? "entidad-row entidad-row-selected"
                        : "entidad-row"
                    }
                    onClick={() => setDocumentoSeleccionadoId(documento.id)}
                  >
                    <td>{documento.dependencia}</td>
                    <td>{documento.nro_documento}</td>
                    <td>{documento.estado_documento}</td>
                    <td>{documento.fecha_tramite}</td>
                    <td>{documento.fecha_respuesta}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {documentoSeleccionado ? (
          <p className="entidad-selected-info">
            Documento seleccionado: <strong>{documentoSeleccionado.nro_documento}</strong>
          </p>
        ) : null}

        {error ? <div className="entidad-message entidad-message-error">{error}</div> : null}
        {mensaje ? <div className="entidad-message entidad-message-ok">{mensaje}</div> : null}

        <div className="entidad-actions">
          <button
            type="button"
            className="entidad-action-button"
            onClick={() => void handleVerificarFirma()}
            disabled={!documentoSeleccionado || cargando}
          >
            Verificacion Firma
          </button>

          <button
            type="button"
            className="entidad-action-button"
            onClick={() => void handleDescargarDocumento()}
            disabled={!documentoSeleccionado || cargando}
          >
            Descarga Documento
          </button>

          <button
            type="button"
            className="entidad-action-button"
            onClick={() => void handleBorrarDocumento()}
            disabled={!documentoSeleccionado || cargando}
          >
            Borrar Documento
          </button>

          <button
            type="button"
            className="entidad-action-button"
            onClick={() => void handleAceptarDocumento()}
            disabled={!puedeResolver}
          >
            Aceptar
          </button>

          <button
            type="button"
            className="entidad-action-button"
            onClick={() => setMostrarFormularioRechazo((actual) => !actual)}
            disabled={!puedeResolver}
          >
            Rechazar
          </button>
        </div>

        {mostrarFormularioRechazo ? (
          <div className="entidad-rechazo-form">
            <label className="entidad-label" htmlFor="motivo-rechazo">
              Motivo del rechazo
            </label>
            <textarea
              id="motivo-rechazo"
              className="entidad-textarea"
              value={motivoRechazo}
              onChange={(event) => setMotivoRechazo(event.target.value)}
              rows={3}
              required
            />
            <button
              type="button"
              className="entidad-action-button"
              onClick={() => void handleRechazarDocumento()}
              disabled={cargando || !motivoRechazo.trim()}
            >
              Confirmar rechazo
            </button>
          </div>
        ) : null}
      </section>
    </main>
  );
}
