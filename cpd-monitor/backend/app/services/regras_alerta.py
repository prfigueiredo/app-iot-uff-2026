"""
Alert conditions (V2), as pure functions: reading + previous levels in,
new levels out. No I/O here, which keeps every rule easy to test.

Conditions are documented in docs/v2-condicoes-de-alerta.md.
"""
from datetime import datetime
from enum import IntEnum

from app.core.config import settings


class Nivel(IntEnum):
    NORMAL = 0
    ATENCAO = 1
    CRITICO = 2


TEMPERATURA = "temperatura"
UMIDADE = "umidade"
AR_DESLIGADO = "ar_desligado"
SEM_COMUNICACAO = "sem_comunicacao"

CONDICOES = (TEMPERATURA, UMIDADE, AR_DESLIGADO, SEM_COMUNICACAO)


def nivel_por_limites(
    valor: float | None, anterior: Nivel, atencao: float, critico: float, histerese: float
) -> Nivel:
    """A level is entered above its limit but only left once the value drops
    histerese below it, so a value hovering around a limit does not flap."""
    if valor is None:
        return anterior
    if valor > critico or (anterior == Nivel.CRITICO and valor > critico - histerese):
        return Nivel.CRITICO
    if valor > atencao or (anterior >= Nivel.ATENCAO and valor > atencao - histerese):
        return Nivel.ATENCAO
    return Nivel.NORMAL


def sensor_sem_comunicacao(leitura: dict, agora: datetime, monitorando_desde: datetime) -> bool:
    """True when the last reading is too old. With no reading at all, the
    timeout counts from when monitoring started."""
    ultima = leitura.get("temperatura_atualizada_em")
    referencia = datetime.fromisoformat(ultima) if ultima else monitorando_desde
    return (agora - referencia).total_seconds() > settings.SENSOR_SEM_COMUNICACAO_S


def avaliar(
    leitura: dict, anteriores: dict[str, Nivel], agora: datetime, monitorando_desde: datetime
) -> dict[str, Nivel]:
    return {
        TEMPERATURA: nivel_por_limites(
            leitura.get("temperatura_c"),
            anteriores[TEMPERATURA],
            settings.TEMPERATURA_ATENCAO_C,
            settings.LIMITE_TEMPERATURA_C,
            settings.HISTERESE_TEMPERATURA_C,
        ),
        UMIDADE: nivel_por_limites(
            leitura.get("umidade_pct"),
            anteriores[UMIDADE],
            settings.UMIDADE_ATENCAO_PCT,
            settings.UMIDADE_CRITICA_PCT,
            settings.HISTERESE_UMIDADE_PCT,
        ),
        AR_DESLIGADO: Nivel.CRITICO if leitura.get("ar_condicionado_status") == "desligado" else Nivel.NORMAL,
        SEM_COMUNICACAO: Nivel.CRITICO
        if sensor_sem_comunicacao(leitura, agora, monitorando_desde)
        else Nivel.NORMAL,
    }
