"""Unit tests of the Orion adapter, using a fake Orion (no Docker needed)."""
import asyncio
from datetime import datetime, timezone

import httpx
import pytest
from pydantic import ValidationError

from app.core import mock_db
from app.core.config import settings
from app.services.fiware import sincronizar_ar_condicionado

ENTIDADE = settings.FIWARE_ENTIDADE_AR_CONDICIONADO


def orion_falso(resposta: httpx.Response):
    def responder(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/v2/entities/{ENTIDADE}"
        assert request.url.params["options"] == "keyValues"
        return resposta

    return httpx.AsyncClient(transport=httpx.MockTransport(responder), base_url="http://orion")


def sincronizar(resposta: httpx.Response) -> bool:
    async def executar():
        async with orion_falso(resposta) as client:
            return await sincronizar_ar_condicionado(client)

    return asyncio.run(executar())


def entidade(temperatura, status="ligado", data="2026-10-06T00:46:21.332Z"):
    return httpx.Response(
        200,
        json={"id": ENTIDADE, "type": "ArCondicionado", "temperatura": temperatura, "status": status, "dateModified": data},
    )


def test_leitura_do_orion_vai_para_a_leitura_atual():
    assert sincronizar(entidade(23.4)) is True
    assert mock_db.LEITURA_ATUAL["temperatura_c"] == 23.4
    assert mock_db.LEITURA_ATUAL["ar_condicionado_status"] == "ligado"


def test_hora_da_leitura_e_a_do_orion_convertida_para_hora_local():
    sincronizar(entidade(23.4, data="2026-10-06T00:46:21.332Z"))
    esperado = datetime(2026, 10, 6, 0, 46, 21, 332000, tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
    assert mock_db.LEITURA_ATUAL["temperatura_atualizada_em"] == esperado.isoformat()


def test_sensor_que_ainda_nao_publicou_nao_inventa_valor():
    antes = dict(mock_db.LEITURA_ATUAL)
    assert sincronizar(httpx.Response(404, json={"error": "NotFound"})) is False
    assert mock_db.LEITURA_ATUAL == antes


@pytest.mark.parametrize("temperatura,status", [("quente", "ligado"), (999, "ligado"), (22, "explodiu")])
def test_leitura_invalida_e_recusada_e_mantem_o_ultimo_valor(temperatura, status):
    sincronizar(entidade(22.0))
    with pytest.raises(ValidationError):
        sincronizar(entidade(temperatura, status))
    assert mock_db.LEITURA_ATUAL["temperatura_c"] == 22.0


def test_erro_do_orion_e_propagado_e_mantem_o_ultimo_valor():
    sincronizar(entidade(22.0))
    with pytest.raises(httpx.HTTPStatusError):
        sincronizar(httpx.Response(500))
    assert mock_db.LEITURA_ATUAL["temperatura_c"] == 22.0


def test_simulador_interno_nao_sobrescreve_temperatura():
    sincronizar(entidade(25.0))
    for _ in range(20):
        mock_db.simular_nova_leitura()
    assert mock_db.LEITURA_ATUAL["temperatura_c"] == 25.0
