from __future__ import annotations 
from datetime import datetime

from app.domain.entities import EstadoPunto, Paso
from app.domain.enums import EstadoIncidencia, NivelEscalamiento
from app.domain.eventos import EventoDominio, IncidenciaAbierta, IncidenciaEscalada

def evaluar_punto(estado:EstadoPunto, ahora: datetime) -> list[EventoDominio]:
    punto = estado.punto

    if not punto.activo or punto.en_mantenimiento:
        return []

    if not punto.ventana_operativa.activa_en(ahora.time()):
        return []

    if estado.incidencia_abierta is not None:
        return _evaluar_escalamiento(estado,ahora)

    referencia = estado.ultimo_paso.ocurrido_en if estado.ultimo_paso else None

    if referencia is None:
        return []

    minutos_transcurridos = (ahora - referencia).total_seconds() / 60

    if minutos_transcurridos > punto.umbral.minutos:
        return [IncidenciaAbierta(punto_id=punto.id, ocurrido_en=ahora)]

    return []


def _evaluar_escalamiento(estado: EstadoPunto, ahora:datetime) -> list[EventoDominio]:
    incidencia = estado.incidencia_abierta
    assert incidencia is not None
    assert incidencia.estado != EstadoIncidencia.CERRADA
    plan = estado.plan_escalamineto
    minutos_abierta = incidencia.duracion_minutos(ahora)

    siguiente_nivel = _nivel_para(minutos_abierta, plan)
    if siguiente_nivel == incidencia.nivel:
        return []

    return [
        IncidenciaEscalada(
            incidencia_id=incidencia.id,
            punto_id=estado.punto.id,
            nuevo_nivel=siguiente_nivel,
            ocurrido_en=ahora,
        )
    ]

def _nivel_para(minutos_abierta:float, plan) -> NivelEscalamiento:
    if minutos_abierta >= plan.minuto_a_gerencia:
        return NivelEscalamiento.GERENCIAL

    if minutos_abierta >= plan.minuto_a_supervisor:
        return NivelEscalamiento.SUPERVISOR
    return NivelEscalamiento.INICIAL


def evaluar_cierre_paso(estado: EstadoPunto, paso: Paso, ahora: datetime ) -> list[EventoDominio]:
    from app.domain.eventos import IncidenciaCerrada
    if estado.incidencia_abierta is None:
        return []

    incidencia = estado.incidencia_abierta
    duracion = (paso.ocurrido_en - incidencia.abierto_en).total_seconds() / 60

    return [
        IncidenciaCerrada(
            incidencia_id=incidencia.id,
            punto_id=estado.punto.id,
            paso_id=paso.id,
            duracion_minutos=max(duracion,0),
            guardia_id=paso.guardia_id,
            ocurrido_en=paso.ocurrido_en
        )
    ]