"""Servicio de dominio Mesa de Partes (HU04).

Implementa la logica de "Envio de solicitud del cliente a dependencia":
recibe los datos de derivacion del administrador, asigna la dependencia,
fija ``fecha_ingreso`` con el instante actual (UTC), calcula
``fecha_maxima_respuesta`` por norma (30 dias habiles) y persiste la
solicitud en estado ``Pendiente``.

La capa de rutas se limita a invocar este servicio (SoC / SRP); el
repositorio en memoria es thread-safe y reemplazable por una BD sin
romper el contrato publico (DIP).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache

from src.logging_config import get_logger
from src.modelos.solicitud import (
    DerivacionInput,
    EstadoSolicitud,
    Solicitud,
)
from src.repositorios.solicitud_repo import (
    RepositorioSolicitudEnMemoria,
    SolicitudRepository,
)

logger = get_logger(__name__)

DIAS_HABILES_RESPUESTA: int = 30
WEEKEND: frozenset[int] = frozenset({5, 6})


def sumar_dias_habiles(inicio: date, dias: int) -> date:
    """Suma ``dias`` habiles a ``inicio`` saltando sabados y domingos.

    Iteracion canonica: avanza el cursor un dia y solo descuenta cuando
    el cursor cae en dia laborable (lunes-viernes). No considera
    feriados nacionales: ese requisito puede agregarse inyectando un
    calendario de feriados sin alterar la firma publica.
    """
    if dias < 0:
        raise ValueError("Los dias habiles a sumar deben ser >= 0.")
    cursor: date = inicio
    restantes: int = dias
    while restantes > 0:
        cursor = cursor + timedelta(days=1)
        if cursor.weekday() not in WEEKEND:
            restantes -= 1
    return cursor


def _calcular_fecha_maxima(ahora: datetime) -> datetime:
    """Convierte ``ahora`` + 30 dias habiles a ``datetime`` aware UTC.

    Se fija al final del dia habil (23:59:59) para que la dependencia
    cuente con la jornada completa de la fecha limite.
    """
    fecha_limite: date = sumar_dias_habiles(
        ahora.date(), DIAS_HABILES_RESPUESTA
    )
    return datetime.combine(
        fecha_limite,
        time(hour=23, minute=59, second=59),
        tzinfo=timezone.utc,
    )


class SolicitudService:
    """Coordina el ciclo de vida de las solicitudes (HU04).

    Delega la persistencia a un ``SolicitudRepository`` inyectado; por
    defecto usa el adaptador en memoria (apto para tests y desarrollo).
    En produccion se inyecta ``RepositorioSolicitudSupabase`` sin cambiar
    esta clase (DIP).
    """

    def __init__(self, repo: SolicitudRepository | None = None) -> None:
        self._repo: SolicitudRepository = (
            repo if repo is not None else RepositorioSolicitudEnMemoria()
        )

    def derivar(self, payload: DerivacionInput) -> Solicitud:
        """Deriva una solicitud a la dependencia indicada (HU04)."""
        ahora: datetime = datetime.now(tz=timezone.utc)
        fecha_maxima: datetime = _calcular_fecha_maxima(ahora)

        solicitud: Solicitud = Solicitud(
            usuario_id=payload.usuario_id,
            detalle_solicitud=payload.detalle_solicitud,
            dependencia_asignada=payload.dependencia_asignada,
            fecha_ingreso=ahora,
            fecha_maxima_respuesta=fecha_maxima,
            estado=EstadoSolicitud.PENDIENTE,
        )  # type: ignore

        self._repo.guardar(solicitud)

        logger.info(
            "Solicitud derivada | id=%s | dependencia=%s | "
            "fecha_ingreso=%s | fecha_maxima=%s",
            solicitud.id,
            solicitud.dependencia_asignada.value,
            solicitud.fecha_ingreso.isoformat(),
            solicitud.fecha_maxima_respuesta.isoformat(),
        )
        return solicitud

    def obtener(self, solicitud_id: str) -> Solicitud:
        """Recupera una solicitud por id."""
        return self._repo.obtener_por_id(solicitud_id)

    def listar(self) -> list[Solicitud]:
        """Devuelve todas las solicitudes almacenadas."""
        return self._repo.listar_todas()


@lru_cache(maxsize=1)
def get_solicitud_service() -> SolicitudService:
    """Provee la instancia singleton del servicio (DI para FastAPI)."""
    return SolicitudService()


__all__ = [
    "DIAS_HABILES_RESPUESTA",
    "SolicitudService",
    "get_solicitud_service",
    "sumar_dias_habiles",
]
