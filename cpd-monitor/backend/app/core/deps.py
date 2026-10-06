"""
Dependências de autenticação (usuário logado) e RBAC (controle de acesso por perfil).
"""
import secrets

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.mock_db import USUARIOS, registrar_tentativa_indevida
from app.core.security import decodificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_usuario_atual(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decodificar_token(token)
    if payload is None:
        registrar_tentativa_indevida("desconhecido", "token inválido ou expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    usuario = next((u for u in USUARIOS if u["id"] == int(payload.get("sub"))), None)
    if usuario is None:
        registrar_tentativa_indevida(str(payload.get("sub")), "usuário do token não existe")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return usuario


def exigir_perfil(*perfis_permitidos: str):
    """Dependency factory: garante que o usuário logado tenha um dos perfis permitidos."""

    def checador(usuario: dict = Depends(get_usuario_atual)) -> dict:
        if usuario["perfil"] not in perfis_permitidos:
            registrar_tentativa_indevida(
                usuario["usuario"],
                f"tentou acessar recurso restrito a {perfis_permitidos} com perfil '{usuario['perfil']}'",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seu perfil não tem permissão para acessar este recurso",
            )
        return usuario

    return checador


def exigir_chave_sensor(x_sensor_key: str = Header(default="")):
    """Authenticates sensor devices, which have no user account."""
    if not secrets.compare_digest(x_sensor_key, settings.SENSOR_API_KEY):
        registrar_tentativa_indevida("sensor", "chave de sensor inválida")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave de sensor inválida")