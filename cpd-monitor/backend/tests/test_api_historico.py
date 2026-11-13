"""History routes (V3) and how the monitoring loop feeds them."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.core import mock_db
from app.core.config import settings
from app.main import app
from app.persistencia.repositorio import MediaPeriodo
from app.services.historico import AgregadorDeMedias


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def token(client):
    r = client.post("/auth/login", data={"username": "visualizador", "password": "visual123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def media(inicio, temperatura=22.0, minutos=None):
    return MediaPeriodo(
        inicio=inicio,
        minutos=minutos or settings.HISTORICO_INTERVALO_MIN,
        amostras=10,
        temperatura_media=temperatura,
        temperatura_min=temperatura - 1,
        temperatura_max=temperatura + 1,
    )


def alerta(data, condicao="temperatura"):
    return {
        "titulo": "Temperatura crítica",
        "descricao": "descrição",
        "severidade": "alta",
        "canal": "push",
        "condicao": condicao,
        "data": data.isoformat(),
        "lido": False,
    }


@pytest.mark.parametrize("rota", ["/historico/medias", "/historico/alertas"])
def test_historico_exige_login(client, rota):
    assert client.get(rota).status_code == 401


def test_medias_das_ultimas_horas(client, token, repositorio):
    agora = datetime.now().replace(minute=0, second=0, microsecond=0)
    repositorio.salvar_media(media(agora - timedelta(hours=30), 30.0))  # outside 24 h
    repositorio.salvar_media(media(agora - timedelta(hours=2), 23.0))
    repositorio.salvar_media(media(agora - timedelta(hours=1), 24.0))

    r = client.get("/historico/medias?horas=24", headers=token).json()

    assert r["intervalo_min"] == settings.HISTORICO_INTERVALO_MIN
    assert [m["temperatura_media"] for m in r["medias"]] == [23.0, 24.0]
    assert r["medias"][0]["inicio"] == (agora - timedelta(hours=2)).isoformat()


@pytest.mark.parametrize("horas", [0, 24 * 31 + 1])
def test_periodo_de_medias_fora_do_limite_e_recusado(client, token, horas):
    assert client.get(f"/historico/medias?horas={horas}", headers=token).status_code == 422


def test_alertas_dos_ultimos_dias_e_por_condicao(client, token, repositorio):
    agora = datetime.now()
    repositorio.salvar_alerta(alerta(agora - timedelta(days=10)))  # outside 7 days
    repositorio.salvar_alerta(alerta(agora - timedelta(days=2)))
    repositorio.salvar_alerta(alerta(agora - timedelta(days=1), condicao="umidade"))

    todos = client.get("/historico/alertas?dias=7", headers=token).json()
    so_umidade = client.get("/historico/alertas?dias=7&condicao=umidade", headers=token).json()

    assert len(todos["alertas"]) == 2
    assert todos["limite_atingido"] is False
    assert [a["condicao"] for a in so_umidade["alertas"]] == ["umidade"]


def test_condicao_desconhecida_e_recusada(client, token):
    assert client.get("/historico/alertas?condicao=banana", headers=token).status_code == 422


def test_rota_antiga_de_historico_inventado_nao_existe(client, token):
    assert client.get("/sensores/historico", headers=token).status_code == 404


def test_laco_de_monitoramento_grava_a_media_quando_a_hora_fecha(monkeypatch, repositorio):
    """The loop step that feeds the averages, with a fake clock and fake readings."""
    agora = {"valor": datetime(2026, 10, 26, 10, 30)}

    class RelogioFalso(datetime):
        @classmethod
        def now(cls, tz=None):
            return agora["valor"]

    monkeypatch.setattr(main, "datetime", RelogioFalso)
    monkeypatch.setattr(main, "_agregador", AgregadorDeMedias(60))

    def sensor_publicou(momento, temperatura):
        agora["valor"] = momento
        mock_db.LEITURA_ATUAL.update(
            temperatura_c=temperatura, umidade_pct=50.0, temperatura_atualizada_em=momento.isoformat()
        )

    import asyncio

    for momento, temperatura in [(datetime(2026, 10, 26, 10, 10), 22.0), (datetime(2026, 10, 26, 10, 50), 26.0)]:
        sensor_publicou(momento, temperatura)
        asyncio.run(main._atualizar_historico(leitura_recebida=True))
        asyncio.run(main._atualizar_historico(leitura_recebida=True))  # same reading polled again
    assert repositorio.listar_medias(60, datetime(2026, 10, 26), datetime(2026, 10, 27)) == []

    agora["valor"] = datetime(2026, 10, 26, 11, 0, 1)  # sensor stopped, the clock closes the hour
    asyncio.run(main._atualizar_historico(leitura_recebida=False))

    [gravada] = repositorio.listar_medias(60, datetime(2026, 10, 26), datetime(2026, 10, 27))
    assert gravada.inicio == datetime(2026, 10, 26, 10)
    assert gravada.amostras == 2
    assert gravada.temperatura_media == pytest.approx(24.0)
