"""
Full flow against a real Orion: sensor publishes -> backend reads -> app endpoint.
Skipped when Orion is not running (start it with docker compose in ../fiware).
"""
import asyncio
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.fiware import sincronizar_ar_condicionado


def _orion_no_ar() -> bool:
    try:
        return httpx.get(f"{settings.FIWARE_URL}/version", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _orion_no_ar(), reason="FIWARE Orion não está rodando")


@pytest.fixture
def entidade_de_teste(monkeypatch):
    entidade_id = f"urn:ngsi-ld:ArCondicionado:teste-{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(settings, "FIWARE_ENTIDADE_AR_CONDICIONADO", entidade_id)
    yield entidade_id
    httpx.delete(f"{settings.FIWARE_URL}/v2/entities/{entidade_id}")


def publicar_como_sensor(entidade_id: str, temperatura: float):
    r = httpx.post(
        f"{settings.FIWARE_URL}/v2/entities",
        params={"options": "upsert,keyValues"},
        json={"id": entidade_id, "type": "ArCondicionado", "temperatura": temperatura, "status": "ligado"},
    )
    assert r.status_code == 204


def sincronizar() -> bool:
    async def executar():
        async with httpx.AsyncClient(base_url=settings.FIWARE_URL) as client:
            return await sincronizar_ar_condicionado(client)

    return asyncio.run(executar())


def test_fluxo_sensor_fiware_backend_app(entidade_de_teste):
    client = TestClient(app)
    login = client.post("/auth/login", data={"username": "visualizador", "password": "visual123"})
    token = {"Authorization": f"Bearer {login.json()['access_token']}"}

    for temperatura in (21.0, 24.5, settings.LIMITE_TEMPERATURA_C + 2):
        publicar_como_sensor(entidade_de_teste, temperatura)
        assert sincronizar() is True
        atual = client.get("/sensores/atual", headers=token).json()
        assert atual["temperatura_c"] == temperatura
        assert atual["temperatura_atualizada_em"] is not None

    assert atual["sensor_calor_alerta"] is True
