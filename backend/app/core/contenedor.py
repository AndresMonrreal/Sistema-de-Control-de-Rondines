from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistencia.repos import (
    LectorEstadoPuntosSQL,
    RepositorioIncidenciasSQL,
    RepositorioPasosSQL,
    RepositorioPuntosSQL
)
from app.adapters.reloj_sistema import RelojSistema
from app.application.registrar_paso import RegistroDePasos
from app.application.evaluar_vigilancia import EvaluarVigilancia

reloj = RelojSistema()

def evaluar_vigilancia(sesion: AsyncSession) -> EvaluarVigilancia:
    lector_estado = LectorEstadoPuntosSQL(sesion)
    repo_incidencias = RepositorioIncidenciasSQL(sesion)
    return EvaluarVigilancia(lector_estado, repo_incidencias, reloj)

def registrador_de_pasos(sesion: AsyncSession) -> RegistroDePasos:
    repo_puntos = RepositorioPuntosSQL(sesion)
    repo_pasos = RepositorioPasosSQL(sesion)
    repo_incidencias = RepositorioIncidenciasSQL(sesion)
    return RegistroDePasos(repo_puntos, repo_pasos, repo_incidencias)




