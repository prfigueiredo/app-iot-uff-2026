"""Periodic averages (V3): pure logic, checked at the period boundaries."""
from datetime import datetime

import pytest

from app.services.historico import AgregadorDeMedias


def t(hora, minuto=0, segundo=0):
    return datetime(2026, 10, 26, hora, minuto, segundo)


@pytest.mark.parametrize(
    "minutos,momento,esperado",
    [
        (60, t(10, 59, 59), t(10)),
        (60, t(11, 0, 0), t(11)),
        (15, t(10, 44, 59), t(10, 30)),
        (15, t(10, 45, 0), t(10, 45)),
        (1, t(10, 7, 30), t(10, 7)),
    ],
)
def test_inicio_do_periodo(minutos, momento, esperado):
    assert AgregadorDeMedias(minutos).inicio_do_periodo(momento) == esperado


@pytest.mark.parametrize("minutos", [0, -5, 7, 50])
def test_intervalo_que_nao_divide_o_dia_e_recusado(minutos):
    with pytest.raises(ValueError):
        AgregadorDeMedias(minutos)


def test_hora_so_fecha_quando_chega_leitura_da_hora_seguinte():
    a = AgregadorDeMedias(60)
    assert a.adicionar(t(10, 5), 22.0, 50.0) == []
    assert a.adicionar(t(10, 30), 24.0, 52.0) == []
    assert a.adicionar(t(10, 59, 59), 26.0, 54.0) == []

    fechada = a.adicionar(t(11, 0, 0), 30.0, 60.0)

    assert len(fechada) == 1
    media = fechada[0]
    assert media.inicio == t(10)
    assert media.minutos == 60
    assert media.amostras == 3
    assert media.temperatura_media == pytest.approx(24.0)
    assert (media.temperatura_min, media.temperatura_max) == (22.0, 26.0)
    assert media.umidade_media == pytest.approx(52.0)
    assert (media.umidade_min, media.umidade_max) == (50.0, 54.0)


def test_leitura_que_fecha_a_hora_entra_na_hora_nova():
    a = AgregadorDeMedias(60)
    a.adicionar(t(10, 30), 22.0, None)
    a.adicionar(t(11, 0), 30.0, None)
    nova = a.adicionar(t(12, 0), 20.0, None)[0]
    assert nova.inicio == t(11)
    assert nova.amostras == 1
    assert nova.temperatura_media == 30.0


def test_a_mesma_leitura_lida_varias_vezes_conta_uma_vez():
    # The backend polls every 2 s and the sensor publishes less often.
    a = AgregadorDeMedias(60)
    for _ in range(5):
        a.adicionar(t(10, 10), 22.0, 50.0)
    a.adicionar(t(10, 20), 26.0, 50.0)
    a.adicionar(t(10, 15), 99.0, 50.0)  # older than the last one: ignored
    media = a.adicionar(t(11), 20.0, 50.0)[0]
    assert media.amostras == 2
    assert media.temperatura_media == pytest.approx(24.0)


def test_umidade_ausente_nao_entra_na_media_de_umidade():
    a = AgregadorDeMedias(60)
    a.adicionar(t(10, 1), 22.0, None)
    a.adicionar(t(10, 2), 24.0, 40.0)
    media = a.adicionar(t(11), 20.0, None)[0]
    assert media.amostras == 2
    assert media.amostras_umidade == 1
    assert media.umidade_media == 40.0


def test_sem_nenhuma_umidade_os_campos_de_umidade_ficam_vazios():
    a = AgregadorDeMedias(60)
    a.adicionar(t(10, 1), 22.0, None)
    media = a.adicionar(t(11), 20.0, None)[0]
    assert (media.amostras_umidade, media.umidade_media, media.umidade_min, media.umidade_max) == (0, None, None, None)


def test_sensor_parado_fecha_a_hora_pelo_relogio():
    a = AgregadorDeMedias(60)
    a.adicionar(t(10, 10), 22.0, 50.0)
    assert a.fechar_vencidos(t(10, 59, 59)) == []
    fechada = a.fechar_vencidos(t(11, 0, 0))
    assert [m.inicio for m in fechada] == [t(10)]
    assert a.fechar_vencidos(t(15)) == []  # nothing open anymore


def test_horas_sem_leitura_nao_viram_media_inventada():
    a = AgregadorDeMedias(60)
    a.adicionar(t(10, 10), 22.0, 50.0)
    fechadas = a.adicionar(t(14, 10), 23.0, 50.0)  # sensor was off from 11h to 14h
    assert [m.inicio for m in fechadas] == [t(10)]


def test_media_parcial_do_desligamento_mesclada_com_o_resto_da_hora_e_igual_a_hora_inteira():
    inteira = AgregadorDeMedias(60)
    for minuto, temp in [(5, 20.0), (15, 22.0), (35, 30.0)]:
        inteira.adicionar(t(10, minuto), temp, temp * 2)
    esperada = inteira.esvaziar()[0]

    antes = AgregadorDeMedias(60)
    antes.adicionar(t(10, 5), 20.0, 40.0)
    antes.adicionar(t(10, 15), 22.0, 44.0)
    parcial = antes.esvaziar()[0]  # backend stopped here
    depois = AgregadorDeMedias(60)  # and started again
    depois.adicionar(t(10, 35), 30.0, 60.0)
    resto = depois.esvaziar()[0]

    mesclada = parcial.mesclar(resto)
    assert mesclada.amostras == esperada.amostras == 3
    assert mesclada.temperatura_media == pytest.approx(esperada.temperatura_media)
    assert mesclada.umidade_media == pytest.approx(esperada.umidade_media)
    assert (mesclada.temperatura_min, mesclada.temperatura_max) == (20.0, 30.0)


def test_esvaziar_sem_leitura_nao_gera_media():
    assert AgregadorDeMedias(60).esvaziar() == []
