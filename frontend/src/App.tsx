import { useEffect, useRef, useState, type FormEvent, type ReactElement } from "react";

import { listarDependencias, type DependenciaDb } from "@/api/dependenciasApi";
import {
  buildSignedDownloadUrl,
  buildVisibleDownloadUrl,
  firmarDocumento,
  type SignedDocumentResponse,
} from "@/api/signatureApi";
import {
  buscarTramites,
  registrarTramite,
  type TipoDocumento,
  type TramiteDb,
} from "@/api/tramitesApi";
import { validarCiudadano } from "@/api/validationApi";
import { ApiError } from "@/types/voting";
import type { CiudadanoValidado } from "@/types/ciudadano";

type Screen = "status" | "validation" | "dashboard" | "registration" | "inbox";
type MessageKind = "success" | "warning" | "error" | "info";

interface AppMessage {
  readonly kind: MessageKind;
  readonly text: string;
}

const CAPTCHA_CODE = "r8nm6";



function fullName(user: CiudadanoValidado | null): string {
  if (!user) return "USUARIO NO VALIDADO";
  return `${user.firstname} ${user.lastname}`;
}

function requiereSesion(screen: Screen): boolean {
  return screen !== "status" && screen !== "validation";
}

export default function App(): ReactElement {
  const [screen, setScreen] = useState<Screen>("status");
  const [user, setUser] = useState<CiudadanoValidado | null>(null);
  const [message, setMessage] = useState<AppMessage | null>(null);
  const [termsOpen, setTermsOpen] = useState<boolean>(false);
  const [registrationStep, setRegistrationStep] = useState<1 | 2>(1);

  const showScreen = (nextScreen: Screen): void => {
    if (requiereSesion(nextScreen) && !user) {
      setMessage({ kind: "warning", text: "Primero valida tus datos para ingresar al sistema." });
      setScreen("validation");
      return;
    }

    if (nextScreen === "registration") setRegistrationStep(1);

    setMessage(null);
    setScreen(nextScreen);
  };

  return (
    <div className="app-shell">
      <header className="gov-header">
        <div className="logo-section">
          <span className="logo-text">
            gob<span className="logo-dot-pe">.pe</span>
          </span>
        </div>
        <div className="app-title">Mesa de Partes Virtual</div>
      </header>

      <nav className={`nav-bar ${screen === "status" || screen === "validation" ? "hidden" : ""}`}>
        <div className="nav-links">
          <button className={screen === "dashboard" ? "active" : ""} onClick={() => showScreen("dashboard")}>
            Inicio
          </button>
          <button className={screen === "registration" ? "active" : ""} onClick={() => showScreen("registration")}>
            Registro de Documentos
          </button>
          <button className={screen === "inbox" ? "active" : ""} onClick={() => showScreen("inbox")}>
            Mis Documentos
          </button>
        </div>
        <div className="user-info">
          {user ? `DNI: ${user.dni} | ${fullName(user)}` : "DNI: 066XXXXX | USUARIO NO VALIDADO"}
        </div>
      </nav>

      <main className="container">
        {message && <div className={`app-message ${message.kind}`}>{message.text}</div>}

        {screen === "status" && <StatusScreen onContinue={() => showScreen("validation")} />}

        {screen === "validation" && (
          <ValidationScreen
            onBack={() => showScreen("status")}
            onValidated={(validatedUser) => {
              setUser(validatedUser);
              setMessage({ kind: "success", text: "Datos validados correctamente." });
              setScreen("dashboard");
            }}
            onError={(text) => setMessage({ kind: "error", text })}
            onOpenTerms={() => setTermsOpen(true)}
          />
        )}

        {screen === "dashboard" && <DashboardScreen userName={fullName(user)} onNavigate={showScreen} />}

        {screen === "inbox" && <InboxScreen dni={user?.dni ?? ""} />}

        {screen === "registration" && (
          <RegistrationScreen
            step={registrationStep}
            setStep={setRegistrationStep}
            dni={user?.dni ?? ""}
            onRegistered={() => {
              setMessage({
                kind: "success",
                text: "Documento firmado y tramite registrado correctamente.",
              });
            }}
          />
        )}
      </main>

      <footer className="main-footer">
        &copy; 2026 Registro Nacional de Identificacion y Estado Civil - RENIEC
      </footer>

      <TermsModal
        open={termsOpen}
        onAccept={() => setTermsOpen(false)}
        onClose={() => setTermsOpen(false)}
      />
    </div>
  );
}

function ValidationScreen({
  onBack,
  onValidated,
  onError,
  onOpenTerms,
}: {
  readonly onBack: () => void;
  readonly onValidated: (validatedUser: CiudadanoValidado) => void;
  readonly onError: (text: string) => void;
  readonly onOpenTerms: () => void;
}): ReactElement {
  const [dni, setDni] = useState<string>("");
  const [digit, setDigit] = useState<string>("");
  const [date, setDate] = useState<string>("");
  const [captcha, setCaptcha] = useState<string>("");
  const [termsAccepted, setTermsAccepted] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();

    if (!dni || !digit || !date || !captcha) {
      onError("Complete todos los campos de validacion antes de continuar.");
      return;
    }

    if (!/^\d{8}$/.test(dni)) {
      onError("El DNI debe tener exactamente 8 digitos numericos.");
      return;
    }

    if (!/^\d$/.test(digit)) {
      onError("El digito de verificacion debe tener un solo numero.");
      return;
    }

    if (captcha.toLowerCase() !== CAPTCHA_CODE) {
      onError("El codigo CAPTCHA no coincide.");
      return;
    }

    if (!termsAccepted) {
      onError("Debe aceptar los terminos y condiciones antes de continuar.");
      return;
    }

    setLoading(true);

    try {
      const validatedUser = await validarCiudadano({ dni, digit, date });

      if (!validatedUser) {
        onError("Los datos no coinciden con la base de datos. Verifique DNI, digito o fecha.");
        return;
      }

      onValidated(validatedUser);
    } catch (err) {
      const text = err instanceof ApiError ? err.message : "No se pudo verificar en la base de datos.";
      onError(text);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="screen-block">
      <h2>Validacion de Datos del Ciudadano</h2>
      <p className="screen-description">
        Estimado usuario, para realizar su tramite en linea primero debe validar sus datos.
      </p>

      <form onSubmit={handleSubmit} noValidate>
        <div className="grid-2-cols">
          <div className="form-group">
            <label htmlFor="validation-dni">DNI</label>
            <input
              id="validation-dni"
              type="text"
              value={dni}
              maxLength={8}
              inputMode="numeric"
              placeholder="Ingrese su DNI"
              onChange={(e) => setDni(e.target.value.replace(/\D/g, ""))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="validation-digit">Digito de Verificacion</label>
            <input
              id="validation-digit"
              type="text"
              value={digit}
              maxLength={1}
              inputMode="numeric"
              placeholder="Ingrese el digito"
              onChange={(e) => setDigit(e.target.value.replace(/\D/g, ""))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="validation-date">Fecha de emision del DNI</label>
            <input id="validation-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>

          <div className="form-group">
            <label htmlFor="captcha-input">Codigo CAPTCHA</label>
            <div className="flex-gap-10">
              <div className="captcha-box">{CAPTCHA_CODE}</div>
              <input
                id="captcha-input"
                type="text"
                value={captcha}
                placeholder="Ingrese el texto"
                onChange={(e) => setCaptcha(e.target.value.trim())}
              />
            </div>
          </div>
        </div>

        <div className="terms-container">
          <input
            id="accept-terms"
            type="checkbox"
            checked={termsAccepted}
            onChange={(e) => setTermsAccepted(e.target.checked)}
          />
          <label htmlFor="accept-terms" className="label-inline">
            Acepto los{" "}
            <button type="button" className="link-button" onClick={onOpenTerms}>
              Terminos y condiciones
            </button>
          </label>
        </div>

        <div className="flex-end mt-20">
          <button type="button" className="btn btn-secondary" onClick={onBack}>
            Atras
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Validando..." : "Validar"}
          </button>
        </div>
      </form>
    </section>
  );
}

function StatusScreen({ onContinue }: { readonly onContinue: () => void }): ReactElement {
  return (
    <section className="screen-block">
      <h2>Consultar estado de tramite</h2>
      <p className="screen-description">
        Al realizar un tramite en alguna oficina del Estado, puedes realizar el seguimiento y obtener el reporte actual de un procedimiento administrativo.
      </p>

      <div className="form-group">
        <label htmlFor="doc-type">Seleccione una entidad para su procedimiento:</label>
        <select id="doc-type" defaultValue="RENIEC">
          <option value="RENIEC">RENIEC - Registro Nacional de Identificacion y Estado Civil</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="doc-number">Numero de documento:</label>
        <input id="doc-number" type="text" placeholder="Ingrese numero de documento" />
      </div>

      <div className="flex-end">
        <button type="button" className="btn btn-primary" onClick={onContinue}>
          Consultar el estado del tramite
        </button>
      </div>
    </section>
  );
}

function DashboardScreen({
  userName,
  onNavigate,
}: {
  readonly userName: string;
  readonly onNavigate: (screen: Screen) => void;
}): ReactElement {
  return (
    <section className="screen-block">
      <h2>Mesa de Partes</h2>
      <p>
        Estimado <strong>{userName}</strong>, por este canal virtual podra presentar documentos de forma rapida sin necesidad de acercarse a la Mesa de Partes del RENIEC.
      </p>

      <div className="dashboard-grid dashboard-grid-2">
        <button className="card" onClick={() => onNavigate("registration")}>
          <div className="card-icon">📄</div>
          <h3>Registro de Documento</h3>
          <p>Presente un nuevo tramite</p>
        </button>

        <button className="card" onClick={() => onNavigate("inbox")}>
          <div className="card-icon">📁</div>
          <h3>Mis Documentos</h3>
          <p>Consulte sus tramites realizados</p>
        </button>
      </div>
    </section>
  );
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatDate(value: string): string {
  if (!value) return "-";
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

function InboxScreen({ dni }: { readonly dni: string }): ReactElement {
  const [resultados, setResultados] = useState<readonly TramiteDb[]>([]);
  const [tipoDocumento, setTipoDocumento] = useState<TipoDocumento>("CARTA");
  const [fechaDesde, setFechaDesde] = useState<string>(todayIsoDate());
  const [fechaHasta, setFechaHasta] = useState<string>(todayIsoDate());
  const [consultando, setConsultando] = useState<boolean>(false);
  const [inboxMessage, setInboxMessage] = useState<AppMessage | null>(null);


  const consultarDocumentos = async (): Promise<void> => {
    setInboxMessage(null);
    setResultados([]);

    if (!dni) {
      setInboxMessage({
        kind: "error",
        text: "No se encontro el DNI del usuario logeado.",
      });
      return;
    }

    if (!fechaDesde || !fechaHasta) {
      setInboxMessage({
        kind: "warning",
        text: "Debe seleccionar Fecha Desde y Fecha Hasta.",
      });
      return;
    }

    if (fechaHasta < fechaDesde) {
      setInboxMessage({
        kind: "warning",
        text: "La Fecha Hasta debe ser mayor o igual a la Fecha Desde.",
      });
      return;
    }

    setConsultando(true);

    try {
      const data = await buscarTramites({
        dni,
        tipo_documento: tipoDocumento,
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta,
      });

      setResultados(data);

      if (data.length === 0) {
        setInboxMessage({
          kind: "info",
          text: "No se encontraron documentos tramitados con los filtros seleccionados.",
        });
      }
    } catch (err) {
      const text =
        err instanceof Error
          ? err.message
          : "No se pudo consultar la base de datos.";

      setInboxMessage({
        kind: "error",
        text,
      });
    } finally {
      setConsultando(false);
    }
  };

  return (
    <section className="screen-block">
      <h2>Bandeja de mis documentos tramitados</h2>

      {inboxMessage && (
        <div className={`app-message ${inboxMessage.kind}`}>{inboxMessage.text}</div>
      )}


      <div className="inbox-filters">
        <div className="form-group form-group-no-margin">
          <label htmlFor="filter-document-type">Filtro del documento</label>
          <select
            id="filter-document-type"
            value={tipoDocumento}
            onChange={(e) => setTipoDocumento(e.target.value as TipoDocumento)}
          >
            <option value="CARTA">CARTA</option>
            <option value="SOLICITUD">SOLICITUD</option>
            <option value="OFICIO">OFICIO</option>
          </select>
        </div>

        <div className="form-group form-group-no-margin">
          <label htmlFor="date-from">Fecha Desde</label>
          <input
            id="date-from"
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
          />
        </div>

        <div className="form-group form-group-no-margin">
          <label htmlFor="date-to">Fecha Hasta</label>
          <input
            id="date-to"
            type="date"
            value={fechaHasta}
            min={fechaDesde}
            onChange={(e) => setFechaHasta(e.target.value)}
          />
        </div>
      </div>

      <div className="flex-end mt-20">
        <button
          className="btn btn-accent"
          type="button"
          disabled={consultando}
          onClick={() => void consultarDocumentos()}
        >
          {consultando ? "Consultando..." : "Consultar 🔍"}
        </button>
      </div>

      <h3>Busqueda de documentos tramitados</h3>

      {resultados.length === 0 ? (
        <p className="field-help">Realice una consulta para visualizar documentos tramitados.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nro de Documento</th>
              <th>Tipo de documento</th>
              <th>Dependencia</th>
              <th>Estado documento</th>
              <th>Fecha de respuesta</th>
            </tr>
          </thead>
          <tbody>
            {resultados.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.nro_documento}</td>
                <td>{doc.tipo_documento}</td>
                <td>{doc.dependencia}</td>
                <td>{doc.estado_documento}</td>
                <td>{formatDate(doc.fecha_respuesta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function RegistrationScreen({
  step,
  setStep,
  dni,
  onRegistered,
}: {
  readonly step: 1 | 2;
  readonly setStep: (step: 1 | 2) => void;
  readonly dni: string;
  readonly onRegistered: (signedDocument: SignedDocumentResponse) => void;
}): ReactElement {
  const [email, setEmail] = useState<string>("cesarlopezarteaga@gmail.com");
  const [mobile, setMobile] = useState<string>("931157261");
  const [documentType, setDocumentType] = useState<TipoDocumento>("CARTA");
  const [dependencias, setDependencias] = useState<readonly DependenciaDb[]>([]);
  const [dependenciaId, setDependenciaId] = useState<string>("");
  const [loadingDependencias, setLoadingDependencias] = useState<boolean>(false);
  const [fileName, setFileName] = useState<string>("");
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [signing, setSigning] = useState<boolean>(false);
  const [signedFeedback, setSignedFeedback] = useState<SignedDocumentResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const archivoPdfCargado = documentFile !== null;

  useEffect(() => {
    let active = true;

    setLoadingDependencias(true);

    listarDependencias()
      .then((items) => {
        if (!active) return;
        setDependencias(items);
      })
      .catch(() => {
        if (!active) return;
        alert("No se pudieron cargar las dependencias desde Supabase.");
      })
      .finally(() => {
        if (!active) return;
        setLoadingDependencias(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const finishRegistration = async (): Promise<void> => {
    if (!dni) {
      alert("No se encontro el DNI del usuario validado.");
      return;
    }

    if (!dependenciaId) {
      alert("Seleccione la dependencia donde se dirige.");
      return;
    }

    if (!documentFile) {
      alert("Debe cargar el Archivo Principal (PDF) antes de continuar.");
      return;
    }

    const dependenciaSeleccionada = dependencias.find(
      (dependencia) => String(dependencia.id) === dependenciaId,
    );

    if (!dependenciaSeleccionada) {
      alert("La dependencia seleccionada no es valida.");
      return;
    }

    setSigning(true);
    setSignedFeedback(null);

    try {
      const signedDocument = await firmarDocumento({
        dni,
        file: documentFile,
        email,
        dependenciaNombre: dependenciaSeleccionada.nombre,
        documentType,
      });

      const contenedorUrl = buildSignedDownloadUrl(signedDocument.downloadSignedUrl);

      await registrarTramite({
        dni,
        tipo_documento: documentType,
        dependencia: dependenciaSeleccionada.nombre,
        contenedor: contenedorUrl,
      });

      console.log("Documento firmado digitalmente", {
        email,
        mobile,
        documentType,
        dependencia: dependenciaSeleccionada,
        fileName,
        signedDocument,
        contenedorUrl,
        pdfSelladoUrl: buildVisibleDownloadUrl(signedDocument.id),
      });

      setSignedFeedback(signedDocument);
      setDocumentFile(null);
      setFileName("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      onRegistered(signedDocument);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "No se pudo firmar digitalmente el documento.";

      alert(message);
    } finally {
      setSigning(false);
    }
  };

  return (
    <section className="screen-block">
      <h2>Nuevo Registro de Documento</h2>

      <div className="progress-bar">
        <div className={`step ${step >= 1 ? "active" : ""}`}>
          <div className="step-number">1</div>
          <div className="step-label">Datos del Ciudadano</div>
        </div>

        <div className="step-connector" />

        <div className={`step ${step >= 2 ? "active" : ""}`}>
          <div className="step-number">2</div>
          <div className="step-label">Datos del Documento</div>
        </div>
      </div>

      {step === 1 ? (
        <div>
          <h3>Datos del Ciudadano</h3>

          <div className="form-group">
            <label htmlFor="citizen-email">Correo Electronico</label>
            <input
              id="citizen-email"
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="citizen-mobile">Celular</label>
            <input
              id="citizen-mobile"
              type="text"
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
            />
          </div>

          <div className="flex-end mt-20">
            <button type="button" className="btn btn-primary" onClick={() => setStep(2)}>
              Siguiente
            </button>
          </div>
        </div>
      ) : (
        <div>
          <h3>Datos del Documento</h3>

          <div className="form-group">
            <label htmlFor="document-type">Tipo de Documento</label>
            <select
              id="document-type"
              value={documentType}
              onChange={(e) => {
                setDocumentType(e.target.value as TipoDocumento);
                setSignedFeedback(null);
              }}
            >
              <option value="CARTA">CARTA</option>
              <option value="SOLICITUD">SOLICITUD</option>
              <option value="OFICIO">OFICIO</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="document-dependency">Dependencia donde se dirige</label>
            <select
              id="document-dependency"
              value={dependenciaId}
              onChange={(e) => {
                setDependenciaId(e.target.value);
                setSignedFeedback(null);
              }}
              disabled={loadingDependencias || signing}
            >
              <option value="" disabled>
                {loadingDependencias ? "Cargando dependencias..." : "Seleccione una dependencia"}
              </option>

              {dependencias.map((dependencia) => (
                <option key={dependencia.id} value={dependencia.id}>
                  {dependencia.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="document-file">Archivo Principal (PDF)</label>
            <input
              id="document-file"
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              disabled={signing}
              onChange={(e) => {
                const file = e.target.files?.[0];

                if (!file) {
                  setDocumentFile(null);
                  setFileName("");
                  setSignedFeedback(null);
                  return;
                }

                const esPdf =
                  file.type === "application/pdf" ||
                  file.name.toLowerCase().endsWith(".pdf");

                if (!esPdf) {
                  alert("Solo se permite cargar archivos PDF.");
                  e.target.value = "";
                  setDocumentFile(null);
                  setFileName("");
                  setSignedFeedback(null);
                  return;
                }

                setDocumentFile(file);
                setFileName(file.name);
                setSignedFeedback(null);
              }}
            />
            {fileName && <p className="field-help">Archivo seleccionado: {fileName}</p>}
          </div>

          <div className="flex-end mt-20">
            <button type="button" className="btn btn-secondary" onClick={() => setStep(1)} disabled={signing}>
              Atras
            </button>

            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void finishRegistration()}
              disabled={!archivoPdfCargado || signing}
              title={
                archivoPdfCargado
                  ? "Firmar digitalmente el documento"
                  : "Debe cargar un archivo PDF para continuar"
              }
            >
              {signing ? "Firmando..." : "Firma digital de Documento"}
            </button>
          </div>

          {signedFeedback && (
            <div className="signature-result">
              <strong>Documento firmado correctamente.</strong>
              <div className="signature-result-code">Hash: {signedFeedback.hashHex}</div>
              <div className="signature-download-links">
                <a
                  href={buildSignedDownloadUrl(signedFeedback.downloadSignedUrl)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Descargar contenedor .uni-signed
                </a>
                <a
                  href={buildVisibleDownloadUrl(signedFeedback.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Descargar PDF con sello de firma
                </a>
              </div>
              <p className="field-help">
                El archivo PDF se limpió del formulario. El correo se enviará desde el microservicio Java si el SMTP está configurado.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function TermsModal({
  open,
  onAccept,
  onClose,
}: {
  readonly open: boolean;
  readonly onAccept: () => void;
  readonly onClose: () => void;
}): ReactElement | null {
  if (!open) return null;

  return (
    <div className="modal active" role="dialog" aria-modal="true">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Terminos y condiciones</h3>
          <button className="close-modal" type="button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="terms-text">
            <p>
              Mediante Resolucion Jefatural N° 000147-2020/JNAC/RENIEC se implementa la Mesa de Partes Virtual del RENIEC para permitir la presentacion de documentos electronicos durante las 24 horas del dia.
            </p>
            <p>
              El usuario declara que los datos ingresados son verdaderos y acepta que la validacion se realice contra la base local de ciudadanos autorizados para este prototipo.
            </p>
            <p>
              Este entorno es academico y de prueba. No reemplaza los servicios oficiales del RENIEC ni ejecuta tramites reales.
            </p>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" type="button" onClick={onClose}>
            Cerrar
          </button>
          <button className="btn btn-primary" type="button" onClick={onAccept}>
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}
