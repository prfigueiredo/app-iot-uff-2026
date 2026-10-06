"""
Sensores físicos do CPD: ar-condicionado, gerador, presença, umidade, calor.
"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import exigir_chave_sensor, get_usuario_atual
from app.core.mock_db import HISTORICO_SENSORES, LEITURA_ATUAL, registrar_leitura_ar_condicionado

router = APIRouter()


class LeituraArCondicionado(BaseModel):
    temperatura_c: float = Field(ge=-20, le=60)
    status: Literal["ligado", "desligado"] = "ligado"


@router.post("/ar-condicionado", dependencies=[Depends(exigir_chave_sensor)])
def receber_leitura_ar_condicionado(dados: LeituraArCondicionado):
    """Recebe a leitura enviada pelo sensor do ar-condicionado (JSON)."""
    return registrar_leitura_ar_condicionado(dados.temperatura_c, dados.status)


@router.get("/atual")
def leitura_atual(usuario: dict = Depends(get_usuario_atual)):
    """Leitura mais recente de todos os sensores físicos do CPD."""
    return LEITURA_ATUAL


@router.get("/historico")
def historico(limite: int = 48, usuario: dict = Depends(get_usuario_atual)):
    """Histórico de leituras (mockado - uma a cada 30 min nas últimas 24h)."""
    return HISTORICO_SENSORES[-limite:]
