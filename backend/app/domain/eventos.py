from __future__ import annotations
from dataclasses import dataclass 
from datetime import datetime

from app.domain.enums import NivelEscalamiento, TipoAlarma

@dataclass(slots=True)
class IncidenciaAbierta:
    punto_id: str
    ocurrido_en: datetime
    tipo_alerta: TipoAlarma.PUNTO_SIN_REVISAR

@dataclass(slots=True)
class IncidenciaEscalada:
    incidencia_id: str
    punto_id: str
    nuevo_nivel: NivelEscalamiento
    ocurrido_en: datetime

@dataclass(slots=True)
class IncidenciaCerrada:
    incidencia_id: str
    punto_id: str
    paso_id: str
    duracion_minutos: float
    guardia_id: str | None
    ocurrido_en: datetime 

EventoDominio = IncidenciaAbierta | IncidenciaEscalada | IncidenciaCerrada
