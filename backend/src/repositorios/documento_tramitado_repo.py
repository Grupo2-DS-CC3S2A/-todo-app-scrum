from __future__ import annotations

from typing import Any, cast

from supabase import Client


class DocumentoTramitadoRepository:
    """Repository Pattern: encapsula el acceso a Supabase."""

    def __init__(self, client: Client) -> None:
        self.client = client

    _COLUMNAS = (
        "id,dni,dependencia,nro_documento,tipo_documento,estado_documento,"
        "fecha_tramite,fecha_respuesta,contenedor,"
        "motivo_rechazo,fecha_resolucion"
    )

    def listar_por_dependencia(self, dependencia: str) -> list[dict[str, Any]]:
        response = (
            self.client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .select(self._COLUMNAS)
            .eq("dependencia", dependencia)
            .order("fecha_tramite", desc=True)
            .order("created_at", desc=True)
            .execute()
        )
        return cast(list[dict[str, Any]], response.data or [])

    def listar_todos(self) -> list[dict[str, Any]]:
        response = (
            self.client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .select(self._COLUMNAS)
            .order("fecha_tramite", desc=True)
            .order("created_at", desc=True)
            .execute()
        )
        return cast(list[dict[str, Any]], response.data or [])

    def obtener_por_id(self, tramite_id: int) -> dict[str, Any] | None:
        response = (
            self.client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .select(self._COLUMNAS)
            .eq("id", tramite_id)
            .limit(1)
            .execute()
        )
        rows = cast(list[dict[str, Any]], response.data or [])
        return rows[0] if rows else None

    def borrar_por_id(self, tramite_id: int) -> None:
        (
            self.client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .delete()
            .eq("id", tramite_id)
            .execute()
        )

    def actualizar_resolucion(
        self,
        tramite_id: int,
        estado_documento: str,
        motivo_rechazo: str | None,
        fecha_resolucion: str,
    ) -> dict[str, Any] | None:
        """Resuelve un documento de forma atomica: el UPDATE solo tiene
        efecto si el documento sigue en estado "EN TRAMITE" en ese momento,
        lo que cierra la ventana de carrera entre dos resoluciones casi
        simultaneas."""
        response = (
            self.client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .update(
                {
                    "estado_documento": estado_documento,
                    "motivo_rechazo": motivo_rechazo,
                    "fecha_resolucion": fecha_resolucion,
                }
            )
            .eq("id", tramite_id)
            .eq("estado_documento", "EN TRAMITE")
            .select(self._COLUMNAS)
            .execute()
        )
        rows = cast(list[dict[str, Any]], response.data or [])
        return rows[0] if rows else None

    def actualizar_reemplazo(
        self, tramite_id: int, contenedor: str
    ) -> dict[str, Any] | None:
        """Reabre un tramite RECHAZADO con un documento de reemplazo: el
        UPDATE solo tiene efecto si el tramite sigue en estado "RECHAZADO"
        en ese momento."""
        response = (
            self.client.schema("tramite_documentario")
            .table("documentos_tramitados")
            .update(
                {
                    "contenedor": contenedor,
                    "estado_documento": "EN TRAMITE",
                    "motivo_rechazo": None,
                    "fecha_resolucion": None,
                }
            )
            .eq("id", tramite_id)
            .eq("estado_documento", "RECHAZADO")
            .select(self._COLUMNAS)
            .execute()
        )
        rows = cast(list[dict[str, Any]], response.data or [])
        return rows[0] if rows else None
