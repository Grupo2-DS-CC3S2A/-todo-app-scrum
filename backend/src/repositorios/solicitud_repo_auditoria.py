"""Decorator (Estructural) de auditoria para ``SolicitudRepository``.

Antes de este modulo cada adaptador (en memoria, Supabase) duplicaba su
propio ``logger.info`` dentro de ``guardar()``, mezclando persistencia con
auditoria. ``RepositorioSolicitudConAuditoria`` envuelve cualquier
``SolicitudRepository`` y agrega el registro de auditoria por fuera: los
adaptadores quedan puros (solo persisten) y la auditoria se activa o
desactiva componiendo, sin tocar ninguna clase concreta.

Diferencia con el Proxy de ``ciudadano_repo``: el Decorator AGREGA una
responsabilidad (auditar) manteniendo la semantica de la operacion; el
Proxy CONTROLA el acceso al recurso (cachea para evitar llamadas caras).
"""

from __future__ import annotations

import time

from src.logging_config import get_logger
from src.modelos.solicitud import Dependencia, EstadoSolicitud, Solicitud
from src.repositorios.solicitud_repo import SolicitudRepository

logger = get_logger(__name__)


class RepositorioSolicitudConAuditoria(SolicitudRepository):
    """Envuelve un repositorio y registra auditoria de cada escritura.

    Implementa el mismo puerto ``SolicitudRepository`` que el componente
    envuelto, por lo que es transparente para la capa de servicios y
    componible con cualquier adaptador (incluso con otros decorators).
    """

    def __init__(self, envuelto: SolicitudRepository) -> None:
        self._envuelto = envuelto

    def guardar(self, solicitud: Solicitud) -> Solicitud:
        inicio = time.perf_counter()
        resultado = self._envuelto.guardar(solicitud)
        duracion_ms = (time.perf_counter() - inicio) * 1000
        logger.info(
            "AUDITORIA guardar | id=%s | dependencia=%s | estado=%s | %.1fms",
            resultado.id,
            resultado.dependencia_asignada.value,
            resultado.estado.value,
            duracion_ms,
        )
        return resultado

    def obtener_por_id(self, solicitud_id: str) -> Solicitud:
        return self._envuelto.obtener_por_id(solicitud_id)

    def listar_por_usuario(self, usuario_id: str) -> list[Solicitud]:
        return self._envuelto.listar_por_usuario(usuario_id)

    def listar_por_dependencia(self, dependencia: Dependencia) -> list[Solicitud]:
        return self._envuelto.listar_por_dependencia(dependencia)

    def listar_por_estado(self, estado: EstadoSolicitud) -> list[Solicitud]:
        return self._envuelto.listar_por_estado(estado)

    def listar_todas(self) -> list[Solicitud]:
        return self._envuelto.listar_todas()

    def contar(self) -> int:
        return self._envuelto.contar()


__all__ = ["RepositorioSolicitudConAuditoria"]
