from __future__ import annotations

import uuid

import structlog

from app.core.config import settings
from app.domain.entities import EstadoPunto, Paso
from app.domain.eventos import IncidenciaCerrada
from app.domain.politicas.vigilancia import evaluar_cierre_paso
from app.domain.value_objects import PlanEscalamiento
from app.domain.enums import TipoAlarma
from app.ports.notificador import Aviso
from app.ports.repositorios import (
    RepositorioPasos,
    RepositorioIncidencias,
    RepositorioPuntos,
)

logger =structlog.get_logger()

def _destinatarios_operativo() -> list[str]:
    chat_id = settings.telegram_chat_id_operativo
    return [chat_id] if chat_id else []

class RegistroDePasos:
    def __init__(
        self,
        repo_puntos: RepositorioPuntos,
        repo_pasos: RepositorioPasos,
        repo_incidencias: RepositorioIncidencias,
    ) -> None:
        self._repo_puntos = repo_puntos
        self._repo_pasos = repo_pasos
        self._repo_incidencias = repo_incidencias
        self._plan = PlanEscalamiento(
            minuto_a_supervisor=settings.escalamiento_supervisor_minutos,
            minutos_a_gerencia=settings.escalamiento_gerencia_minutos
        )

    async def registrar(self, paso: Paso) -> Aviso | None:
        es_nuevo = await self._repo_pasos.guardar_si_no_existe(paso)
        if not es_nuevo:
            logger.debug("paso_duplicado_ignorado", evento_id=paso.evento_id_externo)
            return None

        punto = await self._repo_puntos.obtener(paso.punto_id)
        if punto is None:
            logger.warning("paso_de_punto_desconocido", punto_id=paso.punto_id)
            return None

        incidencia_abierta = await self._repo_incidencias.abierta_de(punto.id)
        estado = EstadoPunto(punto, paso, incidencia_abierta, self._plan)

        eventos = evaluar_cierre_paso(estado, paso, paso.ocurrido_en)
        if not eventos:
            return None

        evento = evento[0]
        assert isinstance(evento, IncidenciaCerrada)

        incidencia = incidencia_abierta
        assert incidencia is not None
        incidencia.cerrar(paso)
        await self._repo_incidencias.actualizar(incidencia)

        logger.info(
            "incidencia_cerrada",
            incidencia_id=incidencia.id,
            punto_id=punto.id,
            duracion_min=round(evento.duracion_minutos, 1),
        )

        texto = (
            f"✅ {punto.nombre} atendida. "
            f"Tiempo de respuesta: {evento.duracion_minutos:.0f} min."
        )

        return Aviso(
            tipo=TipoAlarma.INCIDENCIA_ATENDIDA,
            destinatarios=_destinatarios_operativo(),
            texto=texto,
            punto_id=punto.id,
            incidencia_id=incidencia.id,
        )
