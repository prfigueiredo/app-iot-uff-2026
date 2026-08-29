"""
Funções de segurança: hashing de senha e emissão/validação de token JWT.
"""
import hashlib
from datetime import datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings


def hash_senha(senha: str) -> str:
    """Hash simples (sha256) - suficiente para o mock. Trocar por bcrypt/passlib
    ao integrar com base de usuários real."""
    return hashlib.sha256(senha.encode()).hexdigest()


def verificar_senha(senha_texto: str, senha_hash: str) -> bool:
    return hash_senha(senha_texto) == senha_hash


def criar_token(dados: dict) -> str:
    payload = dados.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        print(f"ERRO AO DECODIFICAR TOKEN: {e}")
        return None