import pytest

from app.core import mock_db
from app.core.ws_manager import ws_manager


@pytest.fixture(autouse=True)
def estado_isolado():
    """Restores the in-memory state after each test, since it is global."""
    leitura = dict(mock_db.LEITURA_ATUAL)
    alertas = [dict(a) for a in mock_db.ALERTAS]
    tentativas = list(mock_db.TENTATIVAS_ACESSO_INDEVIDO)
    conexoes = list(ws_manager.conexoes_ativas)
    yield
    mock_db.LEITURA_ATUAL.clear()
    mock_db.LEITURA_ATUAL.update(leitura)
    mock_db.ALERTAS[:] = alertas
    mock_db.TENTATIVAS_ACESSO_INDEVIDO[:] = tentativas
    ws_manager.conexoes_ativas[:] = conexoes
