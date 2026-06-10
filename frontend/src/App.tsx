import { useEffect, useState, type FormEvent, type ReactElement } from "react";

import { validarCiudadano } from "@/api/validationApi";
import { VotingForm } from "@/components/VotingForm";
import { VotingReceipt } from "@/components/VotingReceipt";
import { useVoting } from "@/hooks/useVoting";
import { ApiError } from "@/types/voting";
import type { CiudadanoValidado } from "@/types/ciudadano";

type Screen = "status" | "validation" | "dashboard" | "registration" | "inbox" | "vote";
type MessageKind = "success" | "warning" | "error" | "info";

interface AppMessage {
  readonly kind: MessageKind;
  readonly text: string;
}

const CAPTCHA_CODE = "r8nm6";

const DOCUMENTOS_DEMO = [
  {
    numero: "2024000123",
    tipo: "SOLICITUD",
    asunto: "RECTIFICACION DE DATOS",
    estado: "EN TRAMITE",
    fecha: "22/03/2026",
  },
  {
    numero: "2024000098",
    tipo: "CARTA",
    asunto: "CONSULTA TECNICA",
    estado: "FINALIZADO",
    fecha: "15/03/2026",
  },
] as const;

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

  const { comprobante, cargando, error, votar, reset } = useVoting();

  const showScreen = (nextScreen: Screen): void => {
    if (requiereSesion(nextScreen) && !user) {
      setMessage({ kind: "warning", text: "Primero valida tus datos para ingresar al sistema." });
      setScreen("validation");
      return;
    }
    if (nextScreen === "registration") setRegistrationStep(1);
    if (nextScreen !== "vote") reset();
    setMessage(null);
    setScreen(nextScreen);
  };

  useEffect(() => {
    if (error) {
      setMessage({ kind: "error", text: error.message });
    }
  }, [error]);

  useEffect(() => {
    if (comprobante) {
      setMessage({ kind: "success", text: "Voto registrado correctamente." });
    }
  }, [comprobante]);

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
          <button className={screen === "vote" ? "active vote-link" : "vote-link"} onClick={() => showScreen("vote")}>
            Voto Electronico
          </button>
        </div>
        <div className="user-info">
          {user ? `DNI: ${user.dni} | ${fullName(user)}` : "DNI: 066XXXXX | USUARIO NO VALIDADO"}
        </div>
      </nav>

      <main className={screen === "vote" ? "container container-wide" : "container"}>
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
        {screen === "dashboard" && (
          <DashboardScreen userName={fullName(user)} onNavigate={showScreen} />
        )}
        {screen === "inbox" && <InboxScreen />}
        {screen === "registration" && (
          <RegistrationScreen
            step={registrationStep}
            setStep={setRegistrationStep}
            onRegistered={() => {
              setMessage({ kind: "success", text: "Documento registrado con exito." });
              setScreen("dashboard");
            }}
          />
        )}
        {screen === "vote" && user && (
          <VoteScreen
            user={user}
            comprobante={comprobante}
            cargando={cargando}
            votar={votar}
            onValidationError={(text) => setMessage({ kind: "warning", text })}
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

      <div className="dashboard-grid dashboard-grid-3">
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
        <button className="card card-vote" onClick={() => onNavigate("vote")}>
          <div className="card-icon">🗳️</div>
          <h3>Voto Electronico</h3>
          <p>Emita su voto de forma segura</p>
        </button>
      </div>
    </section>
  );
}

function InboxScreen(): ReactElement {
  return (
    <section className="screen-block">
      <h2>Bandeja de mis documentos tramitados</h2>

      <div className="inbox-filters">
        <div className="form-group form-group-no-margin">
          <label htmlFor="filter-text">Filtro de documentos</label>
          <input id="filter-text" type="text" placeholder="Buscar por numero o asunto" />
        </div>
        <div className="form-group form-group-no-margin">
          <label htmlFor="date-from">Fecha Desde</label>
          <input id="date-from" type="date" />
        </div>
        <div className="form-group form-group-no-margin">
          <label htmlFor="date-to">Fecha Hasta</label>
          <input id="date-to" type="date" />
        </div>
      </div>

      <div className="flex-end mt-20">
        <button className="btn btn-accent" type="button">
          Consultar 🔍
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Nro de Documento</th>
            <th>Tipo Documento</th>
            <th>Asunto</th>
            <th>Estado</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {DOCUMENTOS_DEMO.map((doc) => (
            <tr key={doc.numero}>
              <td>{doc.numero}</td>
              <td>{doc.tipo}</td>
              <td>{doc.asunto}</td>
              <td>{doc.estado}</td>
              <td>{doc.fecha}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function RegistrationScreen({
  step,
  setStep,
  onRegistered,
}: {
  readonly step: 1 | 2;
  readonly setStep: (step: 1 | 2) => void;
  readonly onRegistered: () => void;
}): ReactElement {
  const [email, setEmail] = useState<string>("cesarlopezarteaga@gmail.com");
  const [mobile, setMobile] = useState<string>("931157261");
  const [documentType, setDocumentType] = useState<string>("CARTA");
  const [subject, setSubject] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");

  const finishRegistration = (): void => {
    if (!subject.trim()) {
      alert("Ingrese el asunto del documento.");
      return;
    }
    console.log("Documento registrado", { email, mobile, documentType, subject, fileName });
    onRegistered();
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
            <input id="citizen-email" type="text" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="form-group">
            <label htmlFor="citizen-mobile">Celular</label>
            <input id="citizen-mobile" type="text" value={mobile} onChange={(e) => setMobile(e.target.value)} />
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
            <select id="document-type" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
              <option>CARTA</option>
              <option>SOLICITUD</option>
              <option>OFICIO</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="document-subject">Asunto del Documento</label>
            <input
              id="document-subject"
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Ingrese el asunto"
            />
          </div>
          <div className="form-group">
            <label htmlFor="document-file">Archivo Principal (PDF)</label>
            <input
              id="document-file"
              type="file"
              accept="application/pdf"
              onChange={(e) => setFileName(e.target.files?.[0]?.name ?? "")}
            />
            {fileName && <p className="field-help">Archivo seleccionado: {fileName}</p>}
          </div>
          <div className="flex-end mt-20">
            <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>
              Atras
            </button>
            <button type="button" className="btn btn-primary" onClick={finishRegistration}>
              Finalizar Registro
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function VoteScreen({
  user,
  comprobante,
  cargando,
  votar,
  onValidationError,
}: {
  readonly user: CiudadanoValidado;
  readonly comprobante: ReturnType<typeof useVoting>["comprobante"];
  readonly cargando: boolean;
  readonly votar: ReturnType<typeof useVoting>["votar"];
  readonly onValidationError: (text: string) => void;
}): ReactElement {
  return (
    <section className="vote-layout">
      <div className="vote-panel-left">
        <div className="vote-logo">RENIEC</div>
        <h2>Mesa de Partes</h2>
        <h3>Electronica RENIEC</h3>
        <p>
          Sistema de voto electronico seguro con cifrado SHA-256 y llaves evolutivas para garantizar anonimato e inmutabilidad.
        </p>
        <span>Seguro · Anonimo · Trazable</span>
      </div>

      <div className="vote-panel-right">
        <h2>Registro de Solicitud</h2>
        <p className="screen-description">Ingresa tus datos para emitir tu voto de forma segura.</p>
        <div className="validated-user-box">
          Ciudadano validado: <strong>{fullName(user)}</strong>
        </div>
        <VotingForm
          cargando={cargando}
          dniInicial={user.dni}
          bloquearDni
          onSubmit={votar}
          onValidationError={onValidationError}
        />
        {comprobante && <VotingReceipt comprobante={comprobante} />}
        <p className="legal-note">Sistema protegido bajo normas de la Ley N° 27269 — RENIEC 2026</p>
      </div>
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

