"""Alert routes and the authenticated real-time channel."""
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core import mock_db
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def token_de(client, usuario, senha):
    return client.post("/auth/login", data={"username": usuario, "password": senha}).json()["access_token"]


@pytest.fixture
def admin(client):
    return {"Authorization": f"Bearer {token_de(client, 'admin', 'admin123')}"}


ALERTA = {"titulo": "Teste", "descricao": "Disparado pelo teste", "severidade": "alta", "canal": "push"}


def test_alerta_simulado_fica_salvo_com_id_proprio(client, admin):
    criado = client.post("/alertas/simular", json=ALERTA, headers=admin).json()
    lista = client.get("/alertas", headers=admin).json()
    assert lista[0] == criado
    assert criado["condicao"] is None
    assert criado["id"] not in [a["id"] for a in lista[1:]]


@pytest.mark.parametrize(
    "mudanca",
    [{"severidade": "banana"}, {"canal": "pombo-correio"}, {"titulo": ""}, {"descricao": ""}],
)
def test_alerta_simulado_invalido_e_recusado(client, admin, mudanca):
    assert client.post("/alertas/simular", json=ALERTA | mudanca, headers=admin).status_code == 422


def test_visualizador_nao_simula_alerta(client):
    token = {"Authorization": f"Bearer {token_de(client, 'visualizador', 'visual123')}"}
    assert client.post("/alertas/simular", json=ALERTA, headers=token).status_code == 403


def test_marcar_alerta_como_lido(client, admin):
    alerta_id = mock_db.ALERTAS[0]["id"]
    r = client.post(f"/alertas/{alerta_id}/lido", headers=admin)
    assert r.status_code == 200
    assert r.json()["lido"] is True
    assert next(a for a in client.get("/alertas", headers=admin).json() if a["id"] == alerta_id)["lido"] is True


def test_marcar_alerta_inexistente(client, admin):
    assert client.post("/alertas/999999/lido", headers=admin).status_code == 404


@pytest.mark.parametrize("primeira_mensagem", [{"token": "invalido"}, {"outra": "coisa"}, "nao-e-json"])
def test_websocket_sem_token_valido_e_recusado_e_registrado(client, primeira_mensagem):
    antes = len(mock_db.TENTATIVAS_ACESSO_INDEVIDO)
    with client.websocket_connect("/alertas/ws") as ws:
        if isinstance(primeira_mensagem, dict):
            ws.send_json(primeira_mensagem)
        else:
            ws.send_text(primeira_mensagem)
        with pytest.raises(WebSocketDisconnect) as fechamento:
            ws.receive_json()
    assert fechamento.value.code == 1008
    assert len(mock_db.TENTATIVAS_ACESSO_INDEVIDO) == antes + 1


def test_websocket_com_token_recebe_alertas_em_tempo_real(client, admin):
    with client.websocket_connect("/alertas/ws") as ws:
        ws.send_json({"token": token_de(client, "visualizador", "visual123")})
        assert ws.receive_json() == {"tipo": "autenticado"}
        criado = client.post("/alertas/simular", json=ALERTA, headers=admin).json()
        assert ws.receive_json() == {"tipo": "novo_alerta", "alerta": criado}
