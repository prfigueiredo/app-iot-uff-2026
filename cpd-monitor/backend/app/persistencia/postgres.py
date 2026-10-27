"""
PostgreSQL implementation of the history storage.

Uses psycopg 3 in synchronous mode. The async callers run it in a worker
thread (asyncio.to_thread), because psycopg's async mode does not work with
the event loop Python uses by default on Windows.
"""
from datetime import datetime

from psycopg import conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from app.persistencia.repositorio import MediaPeriodo

ESQUEMA = """
CREATE TABLE IF NOT EXISTS alertas (
    id          SERIAL PRIMARY KEY,
    titulo      TEXT NOT NULL,
    descricao   TEXT NOT NULL,
    severidade  TEXT NOT NULL CHECK (severidade IN ('alta', 'media', 'baixa')),
    canal       TEXT NOT NULL,
    condicao    TEXT,
    data        TIMESTAMP NOT NULL,
    lido        BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS alertas_data_idx ON alertas (data DESC);

CREATE TABLE IF NOT EXISTS medias (
    inicio             TIMESTAMP NOT NULL,
    minutos            INTEGER NOT NULL,
    amostras           INTEGER NOT NULL,
    temperatura_media  DOUBLE PRECISION NOT NULL,
    temperatura_min    DOUBLE PRECISION NOT NULL,
    temperatura_max    DOUBLE PRECISION NOT NULL,
    amostras_umidade   INTEGER NOT NULL,
    umidade_media      DOUBLE PRECISION,
    umidade_min        DOUBLE PRECISION,
    umidade_max        DOUBLE PRECISION,
    PRIMARY KEY (inicio, minutos)
);
"""

# A second save for the same period (backend restarted mid-period) merges with
# the stored row: averages weighted by sample count, extremes kept. All SET
# expressions read the row as it was before this update.
SALVAR_MEDIA = """
INSERT INTO medias AS m (inicio, minutos, amostras, temperatura_media, temperatura_min, temperatura_max,
                         amostras_umidade, umidade_media, umidade_min, umidade_max)
VALUES (%(inicio)s, %(minutos)s, %(amostras)s, %(temperatura_media)s, %(temperatura_min)s, %(temperatura_max)s,
        %(amostras_umidade)s, %(umidade_media)s, %(umidade_min)s, %(umidade_max)s)
ON CONFLICT (inicio, minutos) DO UPDATE SET
    amostras = m.amostras + EXCLUDED.amostras,
    temperatura_media = (m.temperatura_media * m.amostras + EXCLUDED.temperatura_media * EXCLUDED.amostras)
                        / (m.amostras + EXCLUDED.amostras),
    temperatura_min = LEAST(m.temperatura_min, EXCLUDED.temperatura_min),
    temperatura_max = GREATEST(m.temperatura_max, EXCLUDED.temperatura_max),
    amostras_umidade = m.amostras_umidade + EXCLUDED.amostras_umidade,
    umidade_media = CASE WHEN m.amostras_umidade + EXCLUDED.amostras_umidade = 0 THEN NULL ELSE
                        (COALESCE(m.umidade_media, 0) * m.amostras_umidade
                         + COALESCE(EXCLUDED.umidade_media, 0) * EXCLUDED.amostras_umidade)
                        / (m.amostras_umidade + EXCLUDED.amostras_umidade) END,
    umidade_min = LEAST(m.umidade_min, EXCLUDED.umidade_min),
    umidade_max = GREATEST(m.umidade_max, EXCLUDED.umidade_max)
"""

COLUNAS_ALERTA = "id, titulo, descricao, severidade, canal, condicao, data, lido"


class BancoIndisponivel(RuntimeError):
    pass


def _alerta(linha: dict) -> dict:
    return {**linha, "data": linha["data"].isoformat()}


class RepositorioPostgres:
    def __init__(self, url: str, schema: str | None = None, timeout_s: float = 5):
        opcoes = {"options": f"-c search_path={schema}"} if schema else {}
        self._pool = ConnectionPool(url, min_size=1, max_size=4, kwargs={"row_factory": dict_row, **opcoes}, open=False)
        try:
            self._pool.open(wait=True, timeout=timeout_s)
        except PoolTimeout as e:
            self._pool.close()
            # The URL carries the password, so only its address goes into the message.
            destino = conninfo.conninfo_to_dict(url)
            raise BancoIndisponivel(
                f"PostgreSQL indisponível em {destino.get('host')}:{destino.get('port')}/{destino.get('dbname')}. "
                "Suba o banco com 'docker compose up -d' na pasta cpd-monitor/backend."
            ) from e

    def criar_esquema(self) -> None:
        with self._pool.connection() as con:
            con.execute(ESQUEMA)

    def salvar_alerta(self, alerta: dict) -> dict:
        dados = {**alerta, "data": datetime.fromisoformat(alerta["data"])}
        with self._pool.connection() as con:
            linha = con.execute(
                "INSERT INTO alertas (titulo, descricao, severidade, canal, condicao, data, lido) "
                "VALUES (%(titulo)s, %(descricao)s, %(severidade)s, %(canal)s, %(condicao)s, %(data)s, %(lido)s) "
                f"RETURNING {COLUNAS_ALERTA}",
                dados,
            ).fetchone()
        return _alerta(linha)

    def listar_alertas(self, desde=None, ate=None, condicao=None, limite=100) -> list[dict]:
        with self._pool.connection() as con:
            linhas = con.execute(
                f"SELECT {COLUNAS_ALERTA} FROM alertas "
                "WHERE (%(desde)s::timestamp IS NULL OR data >= %(desde)s) "
                "AND (%(ate)s::timestamp IS NULL OR data < %(ate)s) "
                "AND (%(condicao)s::text IS NULL OR condicao = %(condicao)s) "
                "ORDER BY data DESC, id DESC LIMIT %(limite)s",
                {"desde": desde, "ate": ate, "condicao": condicao, "limite": limite},
            ).fetchall()
        return [_alerta(linha) for linha in linhas]

    def marcar_lido(self, alerta_id: int) -> dict | None:
        with self._pool.connection() as con:
            linha = con.execute(
                f"UPDATE alertas SET lido = TRUE WHERE id = %s RETURNING {COLUNAS_ALERTA}", (alerta_id,)
            ).fetchone()
        return _alerta(linha) if linha else None

    def salvar_media(self, media: MediaPeriodo) -> None:
        with self._pool.connection() as con:
            con.execute(SALVAR_MEDIA, media.__dict__)

    def listar_medias(self, minutos: int, desde: datetime, ate: datetime) -> list[MediaPeriodo]:
        with self._pool.connection() as con:
            linhas = con.execute(
                "SELECT * FROM medias WHERE minutos = %s AND inicio >= %s AND inicio < %s ORDER BY inicio",
                (minutos, desde, ate),
            ).fetchall()
        return [MediaPeriodo(**linha) for linha in linhas]

    def fechar(self) -> None:
        self._pool.close()
