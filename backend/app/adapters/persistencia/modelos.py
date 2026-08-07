from __future__ import annotations
from datetime import datetime, time as hora
from sqlalchemy import ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class SitioModel(Base):
    __tablename__ = "sitio"

    id: Mapped[str] = mapped_column(primary_key=True)
    nombre: Mapped[str]


class PuntoControlModel(Base):
    __tablename__ = "punto_control"
    __table_args__= (
        UniqueConstraint("elemento_id_externo", name="uq_elemento_id_externo"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    sitio_id: Mapped[str] = mapped_column(ForeignKey("sitio.id"))
    nombre: Mapped[str]
    nave: Mapped[str]
    elemento_id_externo: Mapped[str]
    umbral_minutos: Mapped[int]
    ventana_inicio: Mapped[hora | None ] = mapped_column(Time, default=None)
    ventana_fin: Mapped[hora | None] = mapped_column(Time, default=None)
    en_mantenimeinto: Mapped[bool] = mapped_column(default=False)
    activo: Mapped[bool] = mapped_column(default=True)


class GuardiaModel(Base):
    __tablename__ = "guardia"

    id: Mapped[str] = mapped_column(primary_key=True)
    sitio_id: Mapped[str] = mapped_column(ForeignKey("sitio.id")) 
    nombre: Mapped[str]
    person_id_externo: Mapped[str]

class PasoModel(Base):
    __tablename__ = "paso"
    __table_args__ = (
        UniqueConstraint("evento_id_externo", name="uq_evento_id_externo"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    punto_id: Mapped[str] = mapped_column(ForeignKey("punto_control.id"))
    guardia_id: Mapped[str | None]
    ocurrido_en: Mapped[datetime]
    evento_id_externo: Mapped[str]
    fue_retransmitido: Mapped[bool] = mapped_column(default=False)

class IncidenciaModel(Base):
    __tablename__ = "incidencia"

    id: Mapped[str] = mapped_column(primary_key=True)
    punto_id: Mapped[str] = mapped_column(ForeignKey("punto_control.id"))
    abierto_en: Mapped[datetime]
    estado: Mapped[str]
    nivel: Mapped[str]
    cerrado_en: Mapped[datetime | None] = mapped_column(default=None)
    cerrada_por_paso_id: Mapped[str | None] = mapped_column(default=None)
    ultimo_aviso_en: Mapped[datetime | None] = mapped_column(default=None)