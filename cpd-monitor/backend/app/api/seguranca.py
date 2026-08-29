"""
Segurança: consulta ao registro de tentativas de acesso indevido.
Restrito ao perfil admin.
"""
from fastapi import APIRouter, Depends

from app.core.deps import exigir_perfil
from app.core.mock_db import TENTATIVAS_ACESSO_INDEVIDO

router = APIRouter()


@router.get("/tentativas-acesso")
def tentativas_acesso_indevido(usuario: dict = Depends(exigir_perfil("admin"))):
    return list(reversed(TENTATIVAS_ACESSO_INDEVIDO))
