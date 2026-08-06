from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import TipoAlarma

@dataclass(frozen=True, slots=True)
class Aviso:
    tipo: TipoAlarma
    destinatarios: list[str]
    texto: str
    punto_id: str | None = None
    incidencia_id: str | None = None

class Notificadoor(Protocol):
    async def enviar(self, aviso: Aviso) -> None:
        ...

