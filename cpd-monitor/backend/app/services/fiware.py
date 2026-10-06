"""
Reads sensor data from the FIWARE Orion Context Broker (NGSI-v2).

Sensors publish their readings to Orion and the backend only reads from it, so
a new sensor only has to publish an entity, with no new backend route.
"""
from datetime import datetime
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.mock_db import registrar_leitura_ar_condicionado


class EntidadeArCondicionado(BaseModel):
    # Orion accepts any JSON, so readings are validated here.
    temperatura: float = Field(ge=-20, le=60)
    status: Literal["ligado", "desligado"] = "ligado"
    dateModified: datetime


async def ler_entidade(client: httpx.AsyncClient, entidade_id: str) -> dict | None:
    """Returns the entity in keyValues format, or None if no sensor published it yet."""
    r = await client.get(
        f"/v2/entities/{entidade_id}",
        params={"options": "keyValues", "attrs": "*,dateModified"},
    )
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


async def sincronizar_ar_condicionado(client: httpx.AsyncClient) -> bool:
    """Copies the latest air conditioning reading from Orion into the backend.
    Returns False while the sensor has not published anything."""
    dados = await ler_entidade(client, settings.FIWARE_ENTIDADE_AR_CONDICIONADO)
    if dados is None:
        return False
    entidade = EntidadeArCondicionado.model_validate(dados)
    # Orion reports UTC. The rest of the backend uses naive local time.
    medido_em = entidade.dateModified.astimezone().replace(tzinfo=None)
    registrar_leitura_ar_condicionado(entidade.temperatura, entidade.status, medido_em)
    return True
