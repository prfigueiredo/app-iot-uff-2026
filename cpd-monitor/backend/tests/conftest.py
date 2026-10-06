import pytest

from app.core import mock_db


@pytest.fixture(autouse=True)
def leitura_isolada():
    """Restores the in-memory reading after each test, since it is global state."""
    copia = dict(mock_db.LEITURA_ATUAL)
    yield
    mock_db.LEITURA_ATUAL.clear()
    mock_db.LEITURA_ATUAL.update(copia)
