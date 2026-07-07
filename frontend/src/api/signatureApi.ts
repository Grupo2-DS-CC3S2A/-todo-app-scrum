export interface SignedDocumentResponse {
  readonly id: number;
  readonly dni: string;
  readonly apellidosNombres: string;
  readonly ubigeo: string;
  readonly originalFileName: string;
  readonly signedFileName: string;
  readonly contentType: string;
  readonly fileSizeBytes: number;
  readonly signedFileSizeBytes: number;
  readonly containerFormat: string;
  readonly pdfStamped: boolean;
  readonly algorithm: string;
  readonly hashHex: string;
  readonly signatureBase64: string;
  readonly certificateIssuer: string;
  readonly downloadSignedUrl: string;
  readonly createdAt: string;
}

const DEFAULT_SIGNATURE_API_URL = "http://localhost:8083";

const SIGNATURE_API_URL: string =
  (import.meta.env.VITE_SIGNATURE_API_URL as string | undefined)?.trim() ||
  DEFAULT_SIGNATURE_API_URL;

export async function firmarDocumento(params: {
  readonly dni: string;
  readonly file: File;
  readonly email: string;
  readonly dependenciaNombre: string;
  readonly documentType: string;
}): Promise<SignedDocumentResponse> {
  const formData = new FormData();
  formData.append("dni", params.dni);
  formData.append("file", params.file);
  formData.append("email", params.email);
  formData.append("dependencia", params.dependenciaNombre);
  formData.append("documentType", params.documentType);

  const response = await fetch(`${SIGNATURE_API_URL}/api/documentos/sign`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "No se pudo firmar digitalmente el documento.");
  }

  return (await response.json()) as SignedDocumentResponse;
}

function buildSignatureUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }

  return `${SIGNATURE_API_URL}${path}`;
}

export function buildSignedDownloadUrl(downloadSignedUrl: string): string {
  return buildSignatureUrl(downloadSignedUrl);
}

export function buildVisibleDownloadUrl(documentId: number): string {
  return buildSignatureUrl(`/api/documentos/${documentId}/download-visible`);
}
