from typing import Protocol

from app.domain.entities import Paso


class FuenteEventos(Protocol):
    async def obtener_pasos_pendientes(self) -> list[Paso]:
        """Traer el siguiente paso de lotes sin confirmar"""
        ...

    async def confirmar_paso(self, ids_procesados:list[str]) -> None:
        """Se llama SIEMPRE después del commit en base de datos, nunca
        antes -- si confirmas primero y el guardado falla, pierdes
        el evento para siempre."""
        ...