"""
Sensores físicos do CPD: ar-condicionado, gerador, presença, umidade, calor.
"""
from fastapi import APIRouter, Depends

from app.core.deps import get_usuario_atual
from app.core.mock_db import HISTORICO_SENSORES, LEITURA_ATUAL

router = APIRouter()


@router.get("/atual")
def leitura_atual(usuario: dict = Depends(get_usuario_atual)):
    """Leitura mais recente de todos os sensores físicos do CPD."""
    return LEITURA_ATUAL


@router.get("/historico")
def historico(limite: int = 48, usuario: dict = Depends(get_usuario_atual)):
    """Histórico de leituras (mockado - uma a cada 30 min nas últimas 24h)."""
    return HISTORICO_SENSORES[-limite:]
