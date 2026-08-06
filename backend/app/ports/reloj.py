from datetime import datetime
#El protocol define la interfaz que debe cumplir un reloj para poder ser usado en la aplicación
from typing import Protocol


class Reloj(Protocol):
    def ahora(self) -> datetime:
        ...