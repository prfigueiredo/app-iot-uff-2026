"""Sensor do ar-condicionado -> backend -> leitura servida ao app."""
import pytest
from fastapi.testclient import TestClient

from app.core import mock_db
from app.core.config import settings
from app.main import app

CHAVE = {"X-Sensor-Key": settings.SENSOR_API_KEY}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def token(client):
    r = client.post("/auth/login", data={"username": "visualizador", "password": "visual123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_leitura_do_sensor_chega_ao_app(client, token):
    r = client.post("/sensores/ar-condicionado", json={"temperatura_c": 23.4, "status": "ligado"}, headers=CHAVE)
    assert r.status_code == 200

    atual = client.get("/sensores/atual", headers=token).json()
    assert atual["temperatura_c"] == 23.4
    assert atual["ar_condicionado_status"] == "ligado"


def test_valor_exibido_muda_quando_o_sensor_muda(client, token):
    for valor in (20.0, 24.5, 21.1):
        client.post("/sensores/ar-condicionado", json={"temperatura_c": valor}, headers=CHAVE)
        assert client.get("/sensores/atual", headers=token).json()["temperatura_c"] == valor


def test_acima_do_limite_aciona_sensor_de_calor(client, token):
    client.post("/sensores/ar-condicionado", json={"temperatura_c": settings.LIMITE_TEMPERATURA_C + 1}, headers=CHAVE)
    assert client.get("/sensores/atual", headers=token).json()["sensor_calor_alerta"] is True

    client.post("/sensores/ar-condicionado", json={"temperatura_c": settings.LIMITE_TEMPERATURA_C - 1}, headers=CHAVE)
    assert client.get("/sensores/atual", headers=token).json()["sensor_calor_alerta"] is False


def test_simulador_interno_nao_sobrescreve_temperatura_do_sensor(client):
    client.post("/sensores/ar-condicionado", json={"temperatura_c": 25.0}, headers=CHAVE)
    for _ in range(20):
        mock_db.simular_nova_leitura()
    assert mock_db.LEITURA_ATUAL["temperatura_c"] == 25.0


def test_chave_invalida_e_recusada_e_registrada(client):
    antes = len(mock_db.TENTATIVAS_ACESSO_INDEVIDO)
    r = client.post("/sensores/ar-condicionado", json={"temperatura_c": 99}, headers={"X-Sensor-Key": "errada"})
    assert r.status_code == 401
    assert len(mock_db.TENTATIVAS_ACESSO_INDEVIDO) == antes + 1


def test_sem_chave_e_recusado(client):
    assert client.post("/sensores/ar-condicionado", json={"temperatura_c": 22}).status_code == 401


@pytest.mark.parametrize(
    "corpo",
    [{"temperatura_c": 999}, {"temperatura_c": "quente"}, {"temperatura_c": 22, "status": "explodiu"}, {}],
)
def test_leitura_invalida_e_recusada(client, corpo):
    assert client.post("/sensores/ar-condicionado", json=corpo, headers=CHAVE).status_code == 422
