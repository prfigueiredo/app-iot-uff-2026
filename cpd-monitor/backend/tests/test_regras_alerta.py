"""Alert conditions as pure functions, checked at their exact boundaries."""
from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.services.regras_alerta import (
    AR_DESLIGADO,
    CONDICOES,
    SEM_COMUNICACAO,
    TEMPERATURA,
    UMIDADE,
    Nivel,
    avaliar,
    nivel_por_limites,
    sensor_sem_comunicacao,
)

N, A, C = Nivel.NORMAL, Nivel.ATENCAO, Nivel.CRITICO
AGORA = datetime(2026, 10, 6, 12, 0, 0)


@pytest.fixture(autouse=True)
def limites_conhecidos(monkeypatch):
    for nome, valor in {
        "TEMPERATURA_ATENCAO_C": 26,
        "LIMITE_TEMPERATURA_C": 28,
        "HISTERESE_TEMPERATURA_C": 0.5,
        "UMIDADE_ATENCAO_PCT": 60,
        "UMIDADE_CRITICA_PCT": 70,
        "HISTERESE_UMIDADE_PCT": 2,
        "SENSOR_SEM_COMUNICACAO_S": 60,
    }.items():
        monkeypatch.setattr(settings, nome, valor)


@pytest.mark.parametrize(
    "valor,anterior,esperado",
    [
        (25.0, N, N),
        (26.0, N, N),  # the limit itself is still normal
        (26.1, N, A),
        (28.0, A, A),
        (28.1, A, C),
        (28.1, N, C),  # can jump straight to critical
        (27.6, C, C),  # hysteresis: stays critical until 27.5
        (27.5, C, A),
        (25.6, A, A),  # hysteresis: stays in attention until 25.5
        (25.5, A, N),
        (25.6, N, N),  # hysteresis only delays leaving, never entering
        (24.0, C, N),
        (None, C, C),  # no reading keeps the previous level
    ],
)
def test_nivel_da_temperatura(valor, anterior, esperado):
    assert nivel_por_limites(valor, anterior, 26, 28, 0.5) == esperado


@pytest.mark.parametrize(
    "umidade,anterior,esperado",
    [(60, N, N), (61, N, A), (71, A, C), (68.5, C, C), (68, C, A), (58, A, N)],
)
def test_umidade_usa_os_proprios_limites(umidade, anterior, esperado):
    leitura = {"umidade_pct": umidade, "temperatura_atualizada_em": AGORA.isoformat()}
    anteriores = {c: N for c in CONDICOES} | {UMIDADE: anterior}
    assert avaliar(leitura, anteriores, AGORA, AGORA)[UMIDADE] == esperado


def test_ar_condicionado_desligado():
    leitura = {"ar_condicionado_status": "desligado", "temperatura_atualizada_em": AGORA.isoformat()}
    assert avaliar(leitura, {c: N for c in CONDICOES}, AGORA, AGORA)[AR_DESLIGADO] == C
    leitura["ar_condicionado_status"] = "ligado"
    assert avaliar(leitura, {c: C for c in CONDICOES}, AGORA, AGORA)[AR_DESLIGADO] == N


@pytest.mark.parametrize("idade_s,esperado", [(0, False), (60, False), (61, True)])
def test_sensor_sem_comunicacao_pela_idade_da_leitura(idade_s, esperado):
    leitura = {"temperatura_atualizada_em": (AGORA - timedelta(seconds=idade_s)).isoformat()}
    assert sensor_sem_comunicacao(leitura, AGORA, AGORA - timedelta(hours=1)) is esperado


@pytest.mark.parametrize("desde_s,esperado", [(59, False), (61, True)])
def test_sem_nenhuma_leitura_conta_desde_o_inicio_do_monitoramento(desde_s, esperado):
    assert sensor_sem_comunicacao({}, AGORA, AGORA - timedelta(seconds=desde_s)) is esperado


def test_leitura_normal_nao_tem_nenhuma_condicao_ativa():
    leitura = {
        "temperatura_c": 22,
        "umidade_pct": 50,
        "ar_condicionado_status": "ligado",
        "temperatura_atualizada_em": AGORA.isoformat(),
    }
    assert avaliar(leitura, {c: N for c in CONDICOES}, AGORA, AGORA) == {c: N for c in CONDICOES}
    assert set(CONDICOES) == {TEMPERATURA, UMIDADE, AR_DESLIGADO, SEM_COMUNICACAO}
