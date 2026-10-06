"""Alert generation: one alert per level change, stored and pushed to the app."""
import asyncio
from datetime import datetime, timedelta

import pytest

from app.core import mock_db
from app.core.config import settings
from app.core.ws_manager import ws_manager
from app.services.alertas import MonitorDeAlertas, estado_para_o_app

INICIO = datetime(2026, 10, 6, 12, 0, 0)


@pytest.fixture(autouse=True)
def limites_conhecidos(monkeypatch):
    monkeypatch.setattr(settings, "TEMPERATURA_ATENCAO_C", 26)
    monkeypatch.setattr(settings, "LIMITE_TEMPERATURA_C", 28)
    monkeypatch.setattr(settings, "HISTERESE_TEMPERATURA_C", 0.5)
    monkeypatch.setattr(settings, "UMIDADE_ATENCAO_PCT", 60)
    monkeypatch.setattr(settings, "UMIDADE_CRITICA_PCT", 70)
    monkeypatch.setattr(settings, "SENSOR_SEM_COMUNICACAO_S", 60)


class Verificador:
    """Feeds readings to a monitor, one second apart, and returns new alerts."""

    def __init__(self):
        self.monitor = MonitorDeAlertas(monitorando_desde=INICIO)
        self.agora = INICIO

    def leitura(self, temperatura=22.0, umidade=50.0, status="ligado", idade_s=0):
        self.agora += timedelta(seconds=1)
        leitura = {
            "temperatura_c": temperatura,
            "umidade_pct": umidade,
            "ar_condicionado_status": status,
            "temperatura_atualizada_em": (self.agora - timedelta(seconds=idade_s)).isoformat(),
        }
        return asyncio.run(self.monitor.verificar(leitura, self.agora))


def titulos(alertas):
    return [a["titulo"] for a in alertas]


def test_leituras_normais_nao_geram_alerta():
    v = Verificador()
    for _ in range(5):
        assert v.leitura() == []


def test_um_alerta_por_mudanca_de_nivel_e_nunca_por_leitura():
    v = Verificador()
    passos = [
        (26.5, ["Temperatura em atenção"]),
        (27.0, []),  # still attention
        (28.5, ["Temperatura crítica"]),
        (29.5, []),  # still critical
        (27.8, []),  # hysteresis keeps it critical
        (27.0, []),  # improved to attention: no alert
        (25.0, ["Temperatura normalizada"]),
        (22.0, []),
    ]
    for temperatura, esperado in passos:
        assert titulos(v.leitura(temperatura=temperatura)) == esperado, temperatura


def test_salto_direto_para_critico_gera_um_unico_alerta():
    v = Verificador()
    alertas = v.leitura(temperatura=31.0)
    assert titulos(alertas) == ["Temperatura crítica"]
    assert alertas[0]["severidade"] == "alta"


def test_umidade_alta_sugere_vazamento():
    v = Verificador()
    alerta = v.leitura(umidade=65)[0]
    assert alerta["titulo"] == "Umidade elevada"
    assert alerta["severidade"] == "media"
    assert "vazamento" in alerta["descricao"]
    assert titulos(v.leitura(umidade=75)) == ["Umidade crítica"]
    assert titulos(v.leitura(umidade=50)) == ["Umidade normalizada"]


def test_ar_condicionado_desligado_e_religado():
    v = Verificador()
    assert titulos(v.leitura(status="desligado")) == ["Ar-condicionado desligado"]
    assert v.leitura(status="desligado") == []
    assert titulos(v.leitura(status="ligado")) == ["Ar-condicionado religado"]


def test_sensor_sem_comunicacao_e_retorno():
    v = Verificador()
    assert titulos(v.leitura(idade_s=61)) == ["Sensor sem comunicação"]
    assert v.leitura(idade_s=62) == []
    assert titulos(v.leitura(idade_s=0)) == ["Sensor voltou a comunicar"]


def test_varias_condicoes_ao_mesmo_tempo():
    v = Verificador()
    alertas = v.leitura(temperatura=30, umidade=80, status="desligado")
    assert set(titulos(alertas)) == {"Temperatura crítica", "Umidade crítica", "Ar-condicionado desligado"}


def test_alerta_gerado_fica_salvo_com_todos_os_campos():
    v = Verificador()
    alerta = v.leitura(temperatura=29)[0]
    assert mock_db.ALERTAS[0] is alerta
    assert alerta["condicao"] == "temperatura"
    assert alerta["lido"] is False
    assert alerta["canal"] == "push"
    datetime.fromisoformat(alerta["data"])
    assert alerta["id"] not in [a["id"] for a in mock_db.ALERTAS[1:]]


def test_alerta_gerado_e_enviado_ao_app_em_tempo_real():
    class ConexaoFalsa:
        def __init__(self):
            self.recebido = []

        async def send_json(self, mensagem):
            self.recebido.append(mensagem)

    conexao = ConexaoFalsa()
    ws_manager.adicionar(conexao)
    alerta = Verificador().leitura(temperatura=29)[0]
    assert conexao.recebido == [{"tipo": "novo_alerta", "alerta": alerta}]


def test_app_recebe_os_mesmos_niveis_que_geram_os_alertas():
    v = Verificador()
    v.leitura(temperatura=29)
    estado = estado_para_o_app(v.monitor.niveis)
    assert estado["niveis_alerta"]["temperatura"] == "critico"
    assert estado["sensor_calor_alerta"] is True

    # Inside the hysteresis band the alert is still open, so the card must agree.
    v.leitura(temperatura=27.8)
    estado = estado_para_o_app(v.monitor.niveis)
    assert estado["niveis_alerta"]["temperatura"] == "critico"
    assert estado["sensor_calor_alerta"] is True

    v.leitura(temperatura=27.0)
    assert estado_para_o_app(v.monitor.niveis)["niveis_alerta"]["temperatura"] == "atencao"
    assert estado_para_o_app(v.monitor.niveis)["sensor_calor_alerta"] is False
