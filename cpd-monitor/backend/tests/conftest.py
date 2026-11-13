import pytest

from app import persistencia
from app.core import mock_db
from app.core.ws_manager import ws_manager
from app.persistencia.repositorio import RepositorioMemoria


@pytest.fixture(autouse=True)
def estado_isolado():
    """Gives each test empty storage and restores the in-memory state after it,
    since that state is global."""
    leitura = dict(mock_db.LEITURA_ATUAL)
    tentativas = list(mock_db.TENTATIVAS_ACESSO_INDEVIDO)
    conexoes = list(ws_manager.conexoes_ativas)
    persistencia.configurar(RepositorioMemoria())
    yield
    persistencia.configurar(None)
    mock_db.LEITURA_ATUAL.clear()
    mock_db.LEITURA_ATUAL.update(leitura)
    mock_db.TENTATIVAS_ACESSO_INDEVIDO[:] = tentativas
    ws_manager.conexoes_ativas[:] = conexoes


@pytest.fixture
def repositorio():
    return persistencia.obter_repositorio()
