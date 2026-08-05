from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time

from app.domain.enums import EstadoIncidencia, NivelEscalamiento
from app.domain.value_objects import Umbral, VentanaOperativa, PlanEscalamiento


@dataclass(slots=True)
class Guardia:
    id: str
    nombre: str
    person_id_externo: str

@dataclass(slots=True)
class PuntoControl:
    id: str
    nombre: str
    nave: str
    elemento_id_externo: str
    umbral: Umbral
    #El field(defualt_factory=VentanaOperativa) permite que cada instancia de PuntoControl tenga su propia instancia de VentanaOperativa,
    #evitando que todas las instancias compartan la misma referencia a un objeto mutable.
    ventana_operativa: VentanaOperativa = field(default_factory=VentanaOperativa)
    en_mantenimiento: bool = False
    activo: bool = True

@dataclass(slots=True)
class Paso:
    id: str
    punto_id: str
    guardia_id: str
    ocurrido_en: datetime
    evento_id_externo: str
    fue_retransmitido: bool = False

@dataclass(slots=True)
class Incidencia:
    id: str
    punto_id: str
    abierto_en: datetime
    estado: EstadoIncidencia = EstadoIncidencia.ABIERTA
    nivel: NivelEscalamiento = NivelEscalamiento.INICIAL
    cerrado_en: datetime | None = None
    cerrada_por_paso_id: str | None = None
    ultimo_aviso_en: datetime | None = None

    def duracion_minutos(self, ahora:datetime) -> float:
        fin = self.cerrado_en or ahora
        #El total_seconds() devuelve la duración en segundos, y luego se divide por 60 para obtener la duración en minutos.
        return (fin - self.abierto_en).total_seconds() / 60

    def cerrar(self,paso: Paso) -> None:
        self.estado = EstadoIncidencia.CERRADA
        self.cerrado_en = paso.ocurrido_en
        self.cerrada_por_paso_id = paso.id 

@dataclass(slots=True)
class EstadoPunto:
    punto:PuntoControl
    ultimo_paso: Paso | None
    incidencia_abierta: Incidencia | None
    plan_escalamineto: PlanEscalamiento 
        

