"""
Sensores físicos do CPD: ar-condicionado, gerador, presença, umidade, calor.
O histórico das leituras fica em /historico.
"""
from fastapi import APIRouter, Depends

from app.core.deps import get_usuario_atual
from app.core.mock_db import LEITURA_ATUAL

router = APIRouter()


@router.get("/atual")
def leitura_atual(usuario: dict = Depends(get_usuario_atual)):
    """Leitura mais recente de todos os sensores físicos do CPD."""
    return LEITURA_ATUAL
