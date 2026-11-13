"""
Histórico (V3): médias periódicas de temperatura e umidade e alertas anteriores.
"""
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.deps import get_usuario_atual
from app.persistencia import obter_repositorio
from app.persistencia.repositorio import Repositorio

router = APIRouter()

LIMITE_ALERTAS = 1000


@router.get("/medias")
def medias(
    horas: int = Query(default=24, ge=1, le=24 * 31),
    usuario: dict = Depends(get_usuario_atual),
    repositorio: Repositorio = Depends(obter_repositorio),
):
    """Médias de temperatura e umidade das últimas `horas`, da mais antiga para a mais nova.
    Cada média cobre `intervalo_min` minutos (60 por padrão). O período em andamento
    ainda não aparece: ele é gravado quando termina."""
    agora = datetime.now()
    lista = repositorio.listar_medias(settings.HISTORICO_INTERVALO_MIN, agora - timedelta(hours=horas), agora)
    return {"intervalo_min": settings.HISTORICO_INTERVALO_MIN, "medias": [m.para_json() for m in lista]}


@router.get("/alertas")
def alertas(
    dias: int = Query(default=7, ge=1, le=366),
    condicao: Literal["temperatura", "umidade", "ar_desligado", "sem_comunicacao"] | None = None,
    usuario: dict = Depends(get_usuario_atual),
    repositorio: Repositorio = Depends(obter_repositorio),
):
    """Alertas dos últimos `dias`, do mais novo para o mais antigo, opcionalmente de uma só condição."""
    desde = datetime.now() - timedelta(days=dias)
    lista = repositorio.listar_alertas(desde=desde, condicao=condicao, limite=LIMITE_ALERTAS)
    return {"alertas": lista, "limite_atingido": len(lista) == LIMITE_ALERTAS}
