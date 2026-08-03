#El __future__ import annotations permite utilizar anotaciones de tipo que hacen referencia a clases que aún no han sido definidas en el momento de la declaración.
#Esto es útil para evitar problemas de referencia circular y mejorar la legibilidad del código, especialmente en casos donde las clases se refieren entre sí.
from __future__ import annotations
#El dataclass es un decorador que se utiliza para crear clases de datos de manera más concisa y legible.
#Permite definir atributos de clase y generar automáticamente métodos especiales como __init__, __repr__
from dataclasses import dataclass
from datetime import time

#El frozen=True indica que la instancia de la clase es inmutable, y el slots=True optimiza el uso de memoria al restringir los atributos de la clase a un conjunto fijo.
@dataclass(frozen=True, slots=True)
class Umbral:
    minutos:int

    def __post_init__(self) -> None:
        if self.minutos <= 0:
            raise ValueError("El umbral de minutos no puede ser negativo.")
    #El @property es un decorador que permite definir un método como una propiedad de la clase, lo que significa que se puede acceder a él como si fuera un atributo.
    @property
    def segundos(self) -> int:
        return self.minutos * 60

@dataclass(frozen=True, slots=True)
class VentanaOperativa:
    inicio: time | None = None
    fin: time | None = None

    def activa_en(self,hora: time) -> bool:
        if self.inicio is None or self.fin is None:
            return True
        if self.inicio <= self.fin:
            return self.inicio <= hora <= self.fin
        else:
            return hora >= self.inicio or hora <= self.fin

@dataclass(frozen=True, slots=True)
class PlanEscalamiento:
    minuto_a_supervisor: int
    minuto_a_gerencia: int

    def __post_init__(self) -> None:
        if self.minuto_A_supervisor >= self.minuto_a_gerencia:
            raise ValueError("El minuto_a_supervisor debe ser menor que el minuto_a_gerencia.")
