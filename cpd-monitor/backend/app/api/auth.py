"""
Autenticação e perfis de acesso.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_usuario_atual
from app.core.mock_db import USUARIOS, registrar_tentativa_indevida
from app.core.security import criar_token, verificar_senha

router = APIRouter()


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Login por usuário/senha. Usuários de teste:
    admin/admin123, operador/operador123, visualizador/visual123"""
    usuario = next((u for u in USUARIOS if u["usuario"] == form.username), None)
    if not usuario or not verificar_senha(form.password, usuario["senha_hash"]):
        registrar_tentativa_indevida(form.username, "usuário ou senha inválidos")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")

    token = criar_token({"sub": str(usuario["id"]), "perfil": usuario["perfil"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": usuario["id"], "nome": usuario["nome"], "usuario": usuario["usuario"], "perfil": usuario["perfil"]},
    }


@router.get("/me")
def me(usuario: dict = Depends(get_usuario_atual)):
    return {"id": usuario["id"], "nome": usuario["nome"], "usuario": usuario["usuario"], "perfil": usuario["perfil"]}