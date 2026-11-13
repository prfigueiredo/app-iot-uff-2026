"""
The storage the backend is using, chosen once at startup (or by the tests).
"""
from app.core.config import settings
from app.persistencia.repositorio import Repositorio, RepositorioMemoria

_repositorio: Repositorio | None = None


def configurar(repositorio: Repositorio | None) -> None:
    global _repositorio
    _repositorio = repositorio


def configurado() -> bool:
    return _repositorio is not None


def obter_repositorio() -> Repositorio:
    if _repositorio is None:
        raise RuntimeError("Armazenamento não configurado: o backend ainda não terminou de iniciar.")
    return _repositorio


def criar_repositorio() -> Repositorio:
    if settings.ARMAZENAMENTO == "memoria":
        return RepositorioMemoria()
    if settings.ARMAZENAMENTO != "postgres":
        raise ValueError(f"ARMAZENAMENTO deve ser 'postgres' ou 'memoria', não '{settings.ARMAZENAMENTO}'")
    from app.persistencia.postgres import RepositorioPostgres

    repositorio = RepositorioPostgres(settings.DATABASE_URL)
    repositorio.criar_esquema()
    return repositorio
