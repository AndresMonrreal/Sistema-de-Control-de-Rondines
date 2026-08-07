from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.entities import Incidencia, Paso, PuntoControl, EstadoPunto
from app.domain.enums import EstadoIncidencia, NivelEscalamiento
from app.domain.value_objects import PlanEscalamiento, PlanEscalamiento, Umbral, VentanaOperativa
from app.adapters.persistencia.modelos import (
    IncidenciaModel,
    PasoModel,
    PuntoControlModel,
)


def _punto_a_entidad(modelo: PuntoControlModel) -> PuntoControl:
    """Traduce una fila de base de datos a la entidad de dominio."""
    return PuntoControl(
        id=modelo.id,
        nombre=modelo.nombre,
        nave=modelo.nave,
        elemento_id_externo=modelo.elemento_id_externo,
        umbral=Umbral(minutos=modelo.umbral_minutos),
        ventana_operativa=VentanaOperativa(
            inicio=modelo.ventana_inicio, fin=modelo.ventana_fin
        ),
        en_mantenimiento=modelo.en_mantenimiento,
        activo=modelo.activo,
    )


class RepositorioPuntosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar_activos(self) -> list[PuntoControl]:
        resultado = await self._sesion.execute(
            select(PuntoControlModel).where(PuntoControlModel.activo.is_(True))
        )
        modelos = resultado.scalars().all()
        return [_punto_a_entidad(m) for m in modelos]

    async def obtener(self, punto_id: str) -> PuntoControl | None:
        modelo = await self._sesion.get(PuntoControlModel, punto_id)
        if modelo is None:
            return None
        return _punto_a_entidad(modelo)


def _paso_a_entidad(modelo: PasoModel) -> Paso:
    return Paso(
        id=modelo.id,
        punto_id=modelo.punto_id,
        guardia_id=modelo.guardia_id,
        ocurrido_en=modelo.ocurrido_en,
        evento_id_externo=modelo.evento_id_externo,
        fue_retransmitido=modelo.fue_retransmitido,
    )


def _paso_a_modelo(paso: Paso) -> PasoModel:
    return PasoModel(
        id=paso.id,
        punto_id=paso.punto_id,
        guardia_id=paso.guardia_id,
        ocurrido_en=paso.ocurrido_en,
        evento_id_externo=paso.evento_id_externo,
        fue_retransmitido=paso.fue_retransmitido,
    )


class RepositorioPasosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def guardar_si_no_existe(self, paso: Paso) -> bool:
        self._sesion.add(_paso_a_modelo(paso))
        try:
            await self._sesion.flush()
        except IntegrityError:
            await self._sesion.rollback()
            return False
        return True

    async def ultimo_paso_de(self, punto_id: str) -> Paso | None:
        resultado = await self._sesion.execute(
            select(PasoModel)
            .where(PasoModel.punto_id == punto_id)
            .order_by(desc(PasoModel.ocurrido_en))
            .limit(1)
        )
        modelo = resultado.scalars().first()
        if modelo is None:
            return None
        return _paso_a_entidad(modelo)


def _incidencia_a_entidad(modelo: IncidenciaModel) -> Incidencia:
    return Incidencia(
        id=modelo.id,
        punto_id=modelo.punto_id,
        abierto_en=modelo.abierto_en,
        estado=EstadoIncidencia(modelo.estado),
        nivel=NivelEscalamiento(modelo.nivel),
        cerrado_en=modelo.cerrado_en,
        cerrada_por_paso_id=modelo.cerrada_por_paso_id,
        ultimo_aviso_en=modelo.ultimo_aviso_en,
    )


def _incidencia_a_modelo(incidencia: Incidencia) -> IncidenciaModel:
    return IncidenciaModel(
        id=incidencia.id,
        punto_id=incidencia.punto_id,
        abierto_en=incidencia.abierto_en,
        estado=incidencia.estado,
        nivel=incidencia.nivel,
        cerrado_en=incidencia.cerrado_en,
        cerrada_por_paso_id=incidencia.cerrada_por_paso_id,
        ultimo_aviso_en=incidencia.ultimo_aviso_en,
    )


class RepositorioIncidenciasSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def abrir(self, incidencia: Incidencia) -> None:
        self._sesion.add(_incidencia_a_modelo(incidencia))
        await self._sesion.flush()

    async def actualizar(self, incidencia: Incidencia) -> None:
        modelo = await self._sesion.get(IncidenciaModel, incidencia.id)
        if modelo is None:
            return
        modelo.estado = incidencia.estado
        modelo.nivel = incidencia.nivel
        modelo.cerrado_en = incidencia.cerrado_en
        modelo.cerrada_por_paso_id = incidencia.cerrada_por_paso_id
        modelo.ultimo_aviso_en = incidencia.ultimo_aviso_en
        await self._sesion.flush()

    async def abierta_de(self, punto_id: str) -> Incidencia | None:
        resultado = await self._sesion.execute(
            select(IncidenciaModel).where(
                IncidenciaModel.punto_id == punto_id,
                IncidenciaModel.estado != EstadoIncidencia.CERRADA,
            )
        )
        modelo = resultado.scalars().first()
        if modelo is None:
            return None
        return _incidencia_a_entidad(modelo)

    async def listar_abiertas(self) -> list[Incidencia]:
        resultado = await self._sesion.execute(
            select(IncidenciaModel).where(
                IncidenciaModel.estado != EstadoIncidencia.CERRADA
            )
        )
        modelos = resultado.scalars().all()
        return [_incidencia_a_entidad(m) for m in modelos]

class LectorEstadoPuntosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._repo_puntos = RepositorioPuntosSQL(sesion)
        self._repo_pasos = RepositorioPasosSQL(sesion)
        self._repo_incidencias = RepositorioIncidenciasSQL(sesion)

    async def estado_de_todos_los_puntos(self) -> list[EstadoPunto]:
        plan = PlanEscalamiento(
            minuto_a_supervisor=settings.escalamiento_supervisor_minutos,
            minuto_a_gerencia=settings.escalamiento_gerencia_minutos,
        )

        puntos = await self._repo_puntos.listar_activos()
        estados: list[EstadoPunto] = []

        for punto in puntos:
            ultimo_paso = await self._repo_pasos.ultimo_paso_de(punto.id)
            incidencia_abierta = await self._repo_incidencias.abierta_de(punto.id)
  
            estados.append(
                EstadoPunto(punto,ultimo_paso,incidencia_abierta,plan )
            )
        return estados

