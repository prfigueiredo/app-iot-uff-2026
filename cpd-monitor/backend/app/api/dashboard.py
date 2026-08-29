"""
Personalização do dashboard: cada usuário escolhe quais métricas, serviços
e tipos de alerta quer ver.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_usuario_atual
from app.core.mock_db import PREFERENCIAS_DASHBOARD

router = APIRouter()

_PADRAO = {"metricas": ["temperatura", "umidade"], "servicos": [], "tipos_alerta": ["alta", "media", "baixa"]}


@router.get("/preferencias")
def obter_preferencias(usuario: dict = Depends(get_usuario_atual)):
    return PREFERENCIAS_DASHBOARD.get(usuario["id"], _PADRAO)


class PreferenciasEntrada(BaseModel):
    metricas: list[str]
    servicos: list[str]
    tipos_alerta: list[str]


@router.put("/preferencias")
def salvar_preferencias(dados: PreferenciasEntrada, usuario: dict = Depends(get_usuario_atual)):
    PREFERENCIAS_DASHBOARD[usuario["id"]] = dados.model_dump()
    return PREFERENCIAS_DASHBOARD[usuario["id"]]
