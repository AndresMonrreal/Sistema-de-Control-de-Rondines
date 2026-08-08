from __future__ import annotations

import uuid
import structlog

from app.core.config import settings
from app.domain.entities import Incidencia, PuntoControl
from app.domain.enums import TipoAlarma
from app.domain.eventos import EventoDominio, IncidenciaAbierta, IncidenciaEscalada
from app.domain.politicas.vigilancia import evaluar_punto
from app.ports.notificador import Aviso
from app.ports.reloj import Reloj
from app.ports.repositorios import LectorEstadoPuntos, RepositorioIncidencias

logger = structlog.get_logger()

def _destinatarios_operativo() -> list[str]:
    chat_id = settings.telegram_chat_id_operativo
    return [chat_id] if chat_id else []

def _destinatarios_escalamineto() -> list[str]:
    chat_id = settings.telegram_chat_id_escalamiento
    return [chat_id] if chat_id else []

class EvaluadorVigilancia:
    def __init__(
            self,
        lector_estado: LectorEstadoPuntos,
        repo_incidencias: RepositorioIncidencias,
        reloj: Reloj,
    ) -> None:
        self._lector_estado = lector_estado
        self._repo_incidencia = repo_incidencias
        self._reloj = reloj

    async def ejecutar(self) -> list[Aviso]:
        ahora = self._reloj.ahora()
        avisos: list[Aviso] = []

        estados = await self._lector_estado.estado_de_todos_los_puntos()

        for estado in estados:
            eventos = evaluar_punto(estado, estado.punto)
            for evento in eventos:
                aviso = await self._aplicar(evento, estado.punto)
                if aviso is not None:
                    avisos.append(aviso)

        return avisos

    async def _aplicar(
            self, evento: EventoDominio, punto: PuntoControl
    ) -> Aviso | None:
        match evento:
            case IncidenciaAbierta():
                incidencia =  Incidencia(
                    id=str(uuid.uuid4()),
                    punto_id=evento.punto_id,
                    abierto_en=evento.ocurrido_en,
                )
                await self._repo_incidencia.abrir(incidencia)
                logger.info(
                    "incidencia_abierta",
                    punto_id=evento.punto_id,
                    incidencia_id=incidencia.id,
                )
                texto = (
                    f"⚠️ {punto.nombre} lleva más de "
                    f"{punto.umbral.minutos} min sin revisión."
                )
                return Aviso (
                    tipo=TipoAlarma.PUNTO_SIN_REVISAR,
                    destinatarios=_destinatarios_operativo(),
                    texto=texto,
                    punto_id=punto.id,
                    incidencia_id=incidencia.id,
                )
            case IncidenciaEscalada():
                incidencia = await self ._repo_incidencia.abierta_de(evento.punto_id)
                if incidencia is None:
                    logger.warning(
                        "escalamiento_sin_incidencia", punto_id=evento.punto_id
                    )
                    return None

                incidencia.nivel = evento.nuevo_nivel
                await self._repo_incidencia.actualizar(incidencia)
                logger.info(
                    "incidencia_escalada",
                    punto_id=evento.punto_id,
                    nivel=evento.nuevo_nivel,
                )
                texto = (
                    f"🔺 {punto.nombre} sigue sin revisión "
                    f"(nivel: {evento.nuevo_nivel})."
                )
                return Aviso(
                    tipo=TipoAlarma.INCIDENCIA_ESCALADA,
                    destinatarios=_destinatarios_escalamineto(),
                    texto=texto,
                    punto_id=punto.id,
                    incidencia_id=incidencia.id,
                )
        return None