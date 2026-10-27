"""
Storage contract (V3), run against both implementations: in memory and the
real PostgreSQL. The PostgreSQL runs use a throwaway schema, never the real
tables, and are skipped when the database is not running (start it with
docker compose in cpd-monitor/backend).
"""
import os
import uuid
from datetime import datetime, timedelta

import psycopg
import pytest

from app.core.config import settings
from app.persistencia.repositorio import MediaPeriodo, RepositorioMemoria

URL_TESTE = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
T0 = datetime(2026, 10, 26, 10, 0)


def _postgres_no_ar() -> bool:
    try:
        psycopg.connect(URL_TESTE, connect_timeout=2).close()
        return True
    except psycopg.OperationalError:
        return False


POSTGRES_NO_AR = _postgres_no_ar()


@pytest.fixture
def schema_temporario():
    nome = f"teste_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(URL_TESTE, autocommit=True) as con:
        con.execute(f"CREATE SCHEMA {nome}")
    yield nome
    with psycopg.connect(URL_TESTE, autocommit=True) as con:
        con.execute(f"DROP SCHEMA {nome} CASCADE")


def _postgres(schema):
    from app.persistencia.postgres import RepositorioPostgres

    repositorio = RepositorioPostgres(URL_TESTE, schema=schema)
    repositorio.criar_esquema()
    return repositorio


@pytest.fixture(
    params=[
        "memoria",
        pytest.param("postgres", marks=pytest.mark.skipif(not POSTGRES_NO_AR, reason="PostgreSQL não está rodando")),
    ]
)
def repo(request):
    if request.param == "memoria":
        yield RepositorioMemoria()
        return
    schema = request.getfixturevalue("schema_temporario")
    repositorio = _postgres(schema)
    yield repositorio
    repositorio.fechar()


def alerta(data: datetime, condicao="temperatura", titulo="Temperatura crítica"):
    return {
        "titulo": titulo,
        "descricao": "descrição",
        "severidade": "alta",
        "canal": "push",
        "condicao": condicao,
        "data": data.isoformat(),
        "lido": False,
    }


def media(inicio, amostras, temp_media, temp_min, temp_max, umid=None, minutos=60):
    return MediaPeriodo(
        inicio=inicio,
        minutos=minutos,
        amostras=amostras,
        temperatura_media=temp_media,
        temperatura_min=temp_min,
        temperatura_max=temp_max,
        amostras_umidade=amostras if umid is not None else 0,
        umidade_media=umid,
        umidade_min=umid,
        umidade_max=umid,
    )


def test_alerta_salvo_recebe_id_e_volta_igual(repo):
    salvo = repo.salvar_alerta(alerta(T0))
    assert isinstance(salvo["id"], int)
    assert salvo == {**alerta(T0), "id": salvo["id"]}
    assert repo.listar_alertas() == [salvo]


def test_cada_alerta_recebe_um_id_diferente(repo):
    ids = {repo.salvar_alerta(alerta(T0))["id"] for _ in range(3)}
    assert len(ids) == 3


def test_alertas_vem_do_mais_novo_para_o_mais_antigo(repo):
    for horas in (1, 3, 2):
        repo.salvar_alerta(alerta(T0 + timedelta(hours=horas)))
    datas = [a["data"] for a in repo.listar_alertas()]
    assert datas == sorted(datas, reverse=True)


def test_filtro_de_periodo_inclui_o_inicio_e_exclui_o_fim(repo):
    for horas in range(5):
        repo.salvar_alerta(alerta(T0 + timedelta(hours=horas)))
    lista = repo.listar_alertas(desde=T0 + timedelta(hours=1), ate=T0 + timedelta(hours=3))
    assert [a["data"] for a in lista] == [(T0 + timedelta(hours=h)).isoformat() for h in (2, 1)]


def test_filtro_por_condicao_e_limite(repo):
    repo.salvar_alerta(alerta(T0, condicao="umidade", titulo="Umidade crítica"))
    for minuto in range(3):
        repo.salvar_alerta(alerta(T0 + timedelta(minutes=minuto)))
    assert {a["condicao"] for a in repo.listar_alertas(condicao="umidade")} == {"umidade"}
    assert len(repo.listar_alertas(limite=2)) == 2


def test_marcar_como_lido(repo):
    salvo = repo.salvar_alerta(alerta(T0))
    assert repo.marcar_lido(salvo["id"])["lido"] is True
    assert repo.listar_alertas()[0]["lido"] is True
    assert repo.marcar_lido(999999) is None


def test_medias_do_periodo_da_mais_antiga_para_a_mais_nova(repo):
    for horas in (2, 0, 1, 5):
        repo.salvar_media(media(T0 + timedelta(hours=horas), 10, 22.0, 21.0, 23.0, umid=50.0))
    repo.salvar_media(media(T0 + timedelta(hours=1), 10, 99.0, 99.0, 99.0, minutos=1))  # another interval
    lista = repo.listar_medias(60, T0, T0 + timedelta(hours=5))
    assert [m.inicio for m in lista] == [T0, T0 + timedelta(hours=1), T0 + timedelta(hours=2)]
    assert lista[0] == media(T0, 10, 22.0, 21.0, 23.0, umid=50.0)


def test_mesma_hora_gravada_duas_vezes_e_mesclada_pelo_numero_de_amostras(repo):
    # Backend restarted mid-hour: 3 readings before, 1 after.
    repo.salvar_media(media(T0, 3, 20.0, 19.0, 21.0, umid=40.0))
    repo.salvar_media(media(T0, 1, 28.0, 28.0, 28.0, umid=60.0))
    [mesclada] = repo.listar_medias(60, T0, T0 + timedelta(hours=1))
    assert mesclada.amostras == 4
    assert mesclada.temperatura_media == pytest.approx(22.0)  # (3 × 20 + 1 × 28) / 4
    assert (mesclada.temperatura_min, mesclada.temperatura_max) == (19.0, 28.0)
    assert mesclada.umidade_media == pytest.approx(45.0)
    assert (mesclada.umidade_min, mesclada.umidade_max) == (40.0, 60.0)


def test_mescla_com_uma_parte_sem_umidade(repo):
    repo.salvar_media(media(T0, 2, 20.0, 20.0, 20.0))
    repo.salvar_media(media(T0, 2, 22.0, 22.0, 22.0, umid=50.0))
    [mesclada] = repo.listar_medias(60, T0, T0 + timedelta(hours=1))
    assert mesclada.amostras_umidade == 2
    assert mesclada.umidade_media == pytest.approx(50.0)


@pytest.mark.skipif(not POSTGRES_NO_AR, reason="PostgreSQL não está rodando")
def test_historico_sobrevive_a_reinicio_do_backend(schema_temporario):
    # Issue #17: alerts used to vanish when the backend restarted.
    antes = _postgres(schema_temporario)
    salvo = antes.salvar_alerta(alerta(T0))
    antes.salvar_media(media(T0, 10, 22.0, 21.0, 23.0))
    antes.fechar()

    depois = _postgres(schema_temporario)
    assert depois.listar_alertas() == [salvo]
    assert depois.listar_medias(60, T0, T0 + timedelta(hours=1))[0].amostras == 10
    depois.fechar()


@pytest.mark.skipif(not POSTGRES_NO_AR, reason="PostgreSQL não está rodando")
def test_banco_recusa_severidade_invalida(schema_temporario):
    repositorio = _postgres(schema_temporario)
    with pytest.raises(psycopg.errors.CheckViolation):
        repositorio.salvar_alerta({**alerta(T0), "severidade": "banana"})
    repositorio.fechar()
