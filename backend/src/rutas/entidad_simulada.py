from __future__ import annotations

import io
import json
import os
import re
import urllib.error
import urllib.request
import zipfile
from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict
from supabase import Client, create_client

from src.config import settings
from src.excepciones.errors import (
    DocumentoYaResueltoError,
    MotivoRechazoRequeridoError,
    PermisoDenegadoError,
)
from src.modelos.usuario import RolUsuario, Usuario
from src.repositorios.documento_tramitado_repo import DocumentoTramitadoRepository
from src.rutas.auth_deps import require_roles

SIGNATURE_SERVICE_URL = os.getenv(
    "SIGNATURE_SERVICE_URL",
    "http://127.0.0.1:8083",
).rstrip("/")


class DocumentoEntidadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    dependencia: str
    nro_documento: str
    estado_documento: str
    fecha_tramite: date
    fecha_respuesta: date
    contenedor: str
    motivo_rechazo: str | None = None
    fecha_resolucion: date | None = None


class VerificacionFirmaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tramite_id: int
    nro_documento: str
    verificacion_correcta: bool
    mensaje: str
    detalle: Any | None = None


class ResolucionDocumentoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: Literal["ACEPTADO", "RECHAZADO"]
    motivo: str | None = None


class SignatureServiceAdapter:
    """Adapter Pattern: adapta el microservicio Java de firma a FastAPI."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def extraer_id_documento_firmado(self, contenedor_url: str) -> int:
        match = re.search(r"/api/documentos/(\d+)/download-signed", contenedor_url)
        if not match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se pudo identificar el documento firmado desde la "
                    "URL del contenedor."
                ),
            )
        return int(match.group(1))

    def verificar_documento_guardado(self, signed_document_id: int) -> dict[str, Any]:
        url = f"{self.base_url}/api/documentos/{signed_document_id}/verify"
        request = urllib.request.Request(url=url, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read().decode("utf-8", errors="replace")
                if not raw.strip():
                    return {"httpStatus": response.status, "verified": True}
                try:
                    body = json.loads(raw)
                except json.JSONDecodeError:
                    body = {"raw": raw}
                body["httpStatus"] = response.status
                return body

        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"El microservicio de firma rechazó la verificación: {body}",
            ) from exc
        except urllib.error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No se pudo conectar con signature-service.",
            ) from exc

    def descargar_bytes(self, url: str) -> bytes:
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except urllib.error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"No se pudo descargar el archivo desde signature-service: {url}"
                ),
            ) from exc

    def url_pdf_visible(self, signed_document_id: int) -> str:
        return f"{self.base_url}/api/documentos/{signed_document_id}/download-visible"


class EntidadSimuladaFacade:
    """Facade Pattern: concentra los casos de uso de la entidad revisora."""

    def __init__(
        self,
        repository: DocumentoTramitadoRepository,
        signature_adapter: SignatureServiceAdapter,
    ) -> None:
        self.repository = repository
        self.signature_adapter = signature_adapter

    def listar_documentos(
        self, dependencia: str | None, usuario: Usuario
    ) -> list[DocumentoEntidadResponse]:
        if usuario.rol == RolUsuario.OPERADOR:
            dependencia = self._dependencia_del_operador(usuario)

        rows = (
            self.repository.listar_por_dependencia(dependencia.strip())
            if dependencia
            else self.repository.listar_todos()
        )
        return [DocumentoEntidadResponse(**row) for row in rows]

    def verificar_firma(
        self, tramite_id: int, usuario: Usuario
    ) -> VerificacionFirmaResponse:
        documento = self._obtener_documento_o_404(tramite_id)
        self._verificar_acceso_dependencia(documento, usuario)

        signed_document_id = self.signature_adapter.extraer_id_documento_firmado(
            documento["contenedor"]
        )
        detalle = self.signature_adapter.verificar_documento_guardado(
            signed_document_id
        )
        correcta = self._interpretar_resultado_verificacion(detalle)

        return VerificacionFirmaResponse(
            tramite_id=int(documento["id"]),
            nro_documento=str(documento["nro_documento"]),
            verificacion_correcta=correcta,
            mensaje=(
                "La verificación de la firma digital es correcta."
                if correcta
                else "La verificación de la firma digital no fue satisfactoria."
            ),
            detalle=detalle,
        )

    def generar_zip_documento(
        self, tramite_id: int, usuario: Usuario
    ) -> tuple[str, bytes]:
        documento = self._obtener_documento_o_404(tramite_id)
        self._verificar_acceso_dependencia(documento, usuario)

        signed_document_id = self.signature_adapter.extraer_id_documento_firmado(
            documento["contenedor"]
        )

        contenedor_bytes = self.signature_adapter.descargar_bytes(
            documento["contenedor"]
        )
        pdf_visible_bytes = self.signature_adapter.descargar_bytes(
            self.signature_adapter.url_pdf_visible(signed_document_id)
        )

        nro_documento = str(documento["nro_documento"])
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zip_file:
            zip_file.writestr(f"{nro_documento}.uni-signed", contenedor_bytes)
            zip_file.writestr(f"{nro_documento}_firmado.pdf", pdf_visible_bytes)

        return f"documento_{nro_documento}.zip", zip_buffer.getvalue()

    def borrar_documento(self, tramite_id: int, usuario: Usuario) -> None:
        documento = self._obtener_documento_o_404(tramite_id)
        self._verificar_acceso_dependencia(documento, usuario)
        self.repository.borrar_por_id(tramite_id)

    def resolver_documento(
        self,
        tramite_id: int,
        decision: str,
        motivo: str | None,
        usuario: Usuario,
    ) -> DocumentoEntidadResponse:
        documento = self._obtener_documento_o_404(tramite_id)
        self._verificar_acceso_dependencia(documento, usuario)

        motivo_normalizado = (motivo or "").strip()
        if decision == "RECHAZADO" and not motivo_normalizado:
            raise MotivoRechazoRequeridoError(
                "Debe indicar un motivo en texto plano para rechazar el documento."
            )

        motivo_final = motivo_normalizado if decision == "RECHAZADO" else None

        actualizado = self.repository.actualizar_resolucion(
            tramite_id,
            decision,
            motivo_final,
            date.today().isoformat(),
        )
        if actualizado is None:
            raise DocumentoYaResueltoError(
                "El documento ya fue resuelto y no puede resolverse de nuevo."
            )
        return DocumentoEntidadResponse(**actualizado)

    def _obtener_documento_o_404(self, tramite_id: int) -> dict[str, Any]:
        documento = self.repository.obtener_por_id(tramite_id)
        if documento is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe el documento tramitado seleccionado.",
            )
        return documento

    @staticmethod
    def _dependencia_del_operador(usuario: Usuario) -> str:
        if not usuario.dependencia_asignada:
            raise PermisoDenegadoError(
                "Su cuenta de operador no tiene una dependencia asignada. "
                "Contacte al administrador."
            )
        return usuario.dependencia_asignada

    @staticmethod
    def _verificar_acceso_dependencia(
        documento: dict[str, Any], usuario: Usuario
    ) -> None:
        if usuario.rol != RolUsuario.OPERADOR:
            return
        dependencia_operador = EntidadSimuladaFacade._dependencia_del_operador(usuario)
        if documento["dependencia"] != dependencia_operador:
            raise PermisoDenegadoError(
                "No tiene acceso a documentos de otra dependencia."
            )

    @staticmethod
    def _interpretar_resultado_verificacion(detalle: Any) -> bool:
        if not isinstance(detalle, dict):
            return True

        keys = (
            "valid",
            "isValid",
            "verified",
            "signatureValid",
            "integrityOk",
            "firmaValida",
            "verificacionCorrecta",
        )

        for key in keys:
            if key in detalle:
                return bool(detalle[key])

        http_status = int(detalle.get("httpStatus", 200))
        return 200 <= http_status < 300


def get_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
    )


def get_facade() -> EntidadSimuladaFacade:
    client = get_client()
    repository = DocumentoTramitadoRepository(client)
    signature_adapter = SignatureServiceAdapter(SIGNATURE_SERVICE_URL)
    return EntidadSimuladaFacade(repository, signature_adapter)


router = APIRouter(
    prefix="/api/entidad-simulada",
    tags=["entidad-simulada"],
)

# Solo admin y operador entran al modulo de entidad revisora; un operador
# ademas queda acotado a su propia dependencia (ver EntidadSimuladaFacade).
_requiere_revisor = require_roles(RolUsuario.ADMIN, RolUsuario.OPERADOR)


@router.get("/documentos", response_model=list[DocumentoEntidadResponse])
async def listar_documentos_por_dependencia(
    dependencia: str | None = Query(None, min_length=1),
    usuario: Usuario = Depends(_requiere_revisor),
) -> list[DocumentoEntidadResponse]:
    return get_facade().listar_documentos(dependencia, usuario)


@router.post(
    "/documentos/{tramite_id}/verificar",
    response_model=VerificacionFirmaResponse,
)
async def verificar_firma_documento(
    tramite_id: int,
    usuario: Usuario = Depends(_requiere_revisor),
) -> VerificacionFirmaResponse:
    return get_facade().verificar_firma(tramite_id, usuario)


@router.get("/documentos/{tramite_id}/download-paquete")
async def descargar_paquete_documento(
    tramite_id: int,
    usuario: Usuario = Depends(_requiere_revisor),
) -> Response:
    filename, zip_bytes = get_facade().generar_zip_documento(tramite_id, usuario)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/documentos/{tramite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def borrar_documento_tramitado(
    tramite_id: int,
    usuario: Usuario = Depends(_requiere_revisor),
) -> Response:
    get_facade().borrar_documento(tramite_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/documentos/{tramite_id}/resolucion",
    response_model=DocumentoEntidadResponse,
)
async def resolver_documento_tramitado(
    tramite_id: int,
    payload: ResolucionDocumentoRequest,
    usuario: Usuario = Depends(_requiere_revisor),
) -> DocumentoEntidadResponse:
    return get_facade().resolver_documento(
        tramite_id, payload.decision, payload.motivo, usuario
    )
