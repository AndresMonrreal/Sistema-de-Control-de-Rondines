#Usamos StrEnum para que los valores de los enums sean cadenas de texto en lugar de enteros, lo que facilita la serialización y deserialización de datos, 
#especialmente cuando se trabaja con APIs o bases de datos. Esto permite que los valores del enum sean más legibles y comprensibles, ya que se representan como cadenas descriptivas en lugar de números.
#El auto permite que los valores del enum se asignen automáticamente, evitando la necesidad de especificar manualmente cada valor. 
#Esto reduce errores y facilita la adición de nuevos valores al enum en el futuro, ya que no es necesario preocuparse por la asignación de valores únicos.
from enum import StrEnum, auto

class EstadoIncidencia(StrEnum):
    ABIERTA = auto()
    CERRADA = auto()
    EN_PROCESO = auto()

class NivelEscalamiento(StrEnum):
    INICIAL = auto()
    SUPERVISOR = auto()
    GERENCIAL = auto()

class TipoAlarma(StrEnum):
    PUNTO_SIN_REVISAR = auto()
    INCIDENCIA_ESCALADA = auto()
    INCIDENCIA_ATENDIDA = auto()
    TERMINAL_FUERA_DE_LINEA = auto()
    TERMINAL_RECONECTADA = auto()

class EstadoTerminal(StrEnum):
    EN_LINEA = auto()
    FUERA_DE_LINEA = auto()
    DESCONOCIDO = auto()

class EstadoEnvio(StrEnum):
    PENDIENTE = auto()
    ENVIADO = auto()
    FALLIDO = auto()
    AGOTADO = auto()