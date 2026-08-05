from datetime import datetime,time,timedelta
import pytest

from app.domain.entities import EstadoPunto, Guardia, Incidencia, Paso, PuntoControl
from app.domain.eventos import IncidenciaCerrada, IncidenciaAbierta, IncidenciaEscalada
from app.domain.enums import EstadoIncidencia, NivelEscalamiento
from app.domain.politicas.vigilancia import evaluar_cierre_paso, evaluar_punto
from app.domain.value_objects import PlanEscalamiento, Umbral, VentanaOperativa

AHORA = datetime(2026,8,3,12,0,0)

PLAN = PlanEscalamiento(minuto_a_supervisor=15, minuto_a_gerencia=30)

def _punto(**overrides) -> PuntoControl:
    base = dict(
        id="punto-1",
        nombre="Nave 7 - Punto B",
        nave="Nave 7",
        elemento_id_externo='ext-1',
        umbral=Umbral(minutos=45),
    )

    base.update(overrides)
    return PuntoControl(**base)


class TestAperturaDeIncidencia:
    def test_no_alarma_antes_del_umbral(self):
        punto = _punto()
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(minutes=44),
            evento_id_externo="e1"
        )

        estado = EstadoPunto(punto,paso,None,PLAN)
        assert evaluar_punto(estado, AHORA) == []

    def test_alarma_justo_despues_del_umbral(self):
        punto = _punto()
        paso = Paso(
             id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(minutes=46),
            evento_id_externo="e1",
        )
        estado = EstadoPunto(punto,paso,None,PLAN)
        eventos = evaluar_punto(estado,AHORA)

        assert len(eventos) == 1
        assert isinstance(eventos[0],IncidenciaAbierta)
        assert eventos[0].punto_id == punto.id

    def test_sin_paso_previo_no_alarma(self):
        punto = _punto()
        estado = EstadoPunto(punto,None,None,PLAN)
        assert evaluar_punto(estado,AHORA) == []

    def test_no_alarma_dos_veces_si_ya_hay_incidencia_abierta(self):
        punto = _punto()
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(minutes=90),
            evento_id_externo="e1",
        )

        incidencia = Incidencia(
            id="i1", punto_id=punto.id, abierto_en=AHORA - timedelta(minutes=5)
        )

        estado = EstadoPunto(punto, paso , incidencia, PLAN)

        eventos = evaluar_punto(estado, AHORA)

        assert not any(isinstance(e, IncidenciaAbierta) for e in eventos)

class TestEscalamiento:
    def test_no_escala_antes_de_tiempo(self):
        punto = _punto()
        incidencia = Incidencia(
            id="i1",
            punto_id=punto.id,
            abierto_en=AHORA - timedelta(minutes=10),
            nivel=NivelEscalamiento.INICIAL,
        )

        estado = EstadoPunto(punto, None, incidencia, PLAN)

        assert evaluar_punto(estado, AHORA) == []


    def test_escala_a_supervisor_a_los_15_min(self):
        punto = _punto()
        incidencia = Incidencia(
            id="i1",
            punto_id=punto.id,
            abierto_en=AHORA - timedelta(minutes=16),
            nivel=NivelEscalamiento.INICIAL,
        )

        estado = EstadoPunto(punto,None,incidencia,PLAN)

        eventos = evaluar_punto(estado, AHORA)
        assert len(eventos) == 1
        assert isinstance(eventos[0], IncidenciaEscalada)
        assert eventos[0].nuevo_nivel == NivelEscalamiento.SUPERVISOR

    def test_escala_a_gerencia_a_los_30_min(self):
        punto = _punto()
        incidencia = Incidencia(
            id="i1",
            punto_id=punto.id,
            abierto_en=AHORA - timedelta(minutes=31),
            nivel=NivelEscalamiento.SUPERVISOR,
        )
        estado = EstadoPunto(punto, None, incidencia, PLAN)

        eventos = evaluar_punto(estado, AHORA)

        assert eventos[0].nuevo_nivel == NivelEscalamiento.GERENCIAL

    def test_no_reescala_si_ya_esta_en_el_nivel_correcto(self):
        punto = _punto()
        incidencia = Incidencia(
            id="i1",
            punto_id=punto.id,
            abierto_en=AHORA - timedelta(minutes=20),
            nivel=NivelEscalamiento.SUPERVISOR,
        )
        estado = EstadoPunto(punto, None, incidencia, PLAN)

        assert evaluar_punto(estado, AHORA) == []


class TestCierrePorPaso:
    def test_paso_nuevo_cierra_la_incidencia(self):
        punto = _punto()
        incidencia = Incidencia(
            id="i1",
            punto_id=punto.id,
            abierto_en=AHORA - timedelta(minutes=27),
            nivel=NivelEscalamiento.SUPERVISOR,
        )
        estado = EstadoPunto(punto, None, incidencia, PLAN)
        paso = Paso(
            id="p-nuevo",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA,
            evento_id_externo="e-nuevo",
        )

        eventos = evaluar_cierre_paso(estado, paso, AHORA)

        assert len(eventos) == 1
        #EL isinstance
        assert isinstance(eventos[0], IncidenciaCerrada)
        assert eventos[0].duracion_minutos == pytest.approx(27, abs=0.1)
        assert eventos[0].guardia_id == "g1"

    def test_sin_incidencia_abierta_no_pasa_nada(self):
        punto = _punto()
        estado = EstadoPunto(punto, None, None, PLAN)
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA,
            evento_id_externo="e1",
        )

        assert evaluar_cierre_paso(estado, paso, AHORA) == []

    def test_duracion_se_ancla_a_la_hora_real_del_evento_no_a_la_recepcion(self):
        punto = _punto()
        incidencia = Incidencia(
            id="i1", punto_id=punto.id, abierto_en=AHORA - timedelta(minutes=60)
        )
        estado = EstadoPunto(punto, None, incidencia, PLAN)
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(minutes=50),
            evento_id_externo="e1",
            fue_retransmitido=True,
        )

        eventos = evaluar_cierre_paso(estado, paso, AHORA)

        assert eventos[0].duracion_minutos == pytest.approx(10, abs=0.1)


class TestPuntoInactivoOMantenimiento:
    def test_punto_en_mantenimiento_no_alarma(self):
        punto = _punto(en_mantenimiento=True)
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(hours=5),
            evento_id_externo="e1",
        )
        estado = EstadoPunto(punto, paso, None, PLAN)

        assert evaluar_punto(estado, AHORA) == []

    def test_punto_inactivo_no_alarma(self):
        punto = _punto(activo=False)
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(hours=5),
            evento_id_externo="e1",
        )
        estado = EstadoPunto(punto, paso, None, PLAN)

        assert evaluar_punto(estado, AHORA) == []


class TestVentanaOperativa:
    def test_fuera_de_ventana_nocturna_no_alarma(self):
        punto = _punto(ventana_operativa=VentanaOperativa(time(20, 0), time(6, 0)))
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=AHORA - timedelta(hours=10),
            evento_id_externo="e1",
        )
        estado = EstadoPunto(punto, paso, None, PLAN)

        assert evaluar_punto(estado, AHORA) == []

    def test_dentro_de_ventana_nocturna_si_alarma(self):
        punto = _punto(ventana_operativa=VentanaOperativa(time(20, 0), time(6, 0)))
        medianoche = datetime(2026, 8, 3, 23, 0, 0)
        paso = Paso(
            id="p1",
            punto_id=punto.id,
            guardia_id="g1",
            ocurrido_en=medianoche - timedelta(minutes=50),
            evento_id_externo="e1",
        )
        estado = EstadoPunto(punto, paso, None, PLAN)

        eventos = evaluar_punto(estado, medianoche)

        assert len(eventos) == 1
        assert isinstance(eventos[0], IncidenciaAbierta)    