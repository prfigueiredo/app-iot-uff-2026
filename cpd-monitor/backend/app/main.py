"""
App de Monitoramento do CPD - STI Niterói-RJ
Ponto de entrada da API backend (FastAPI).
"""
import asyncio
import logging
from datetime import datetime

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app import persistencia
from app.core.config import settings
from app.core.mock_db import LEITURA_ATUAL, simular_nova_leitura
from app.api import auth, sensores, alertas, historico, integracoes, dashboard, seguranca
from app.services.alertas import MonitorDeAlertas, estado_para_o_app, niveis_salvos
from app.services.fiware import sincronizar_ar_condicionado
from app.services.historico import AgregadorDeMedias

log = logging.getLogger("uvicorn.error")

# asyncio keeps only weak references to tasks, so background loops are held here.
_tarefas_em_background: set[asyncio.Task] = set()

_agregador = AgregadorDeMedias(settings.HISTORICO_INTERVALO_MIN)

app = FastAPI(
    title="CPD Monitor API",
    description="API de monitoramento de infraestrutura do CPD (dados simulados/mockados)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["autenticação"])
app.include_router(sensores.router, prefix="/sensores", tags=["sensores físicos"])
app.include_router(alertas.router, prefix="/alertas", tags=["alertas"])
app.include_router(historico.router, prefix="/historico", tags=["histórico"])
app.include_router(integracoes.router, prefix="/integracoes", tags=["graylog/zabbix"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(seguranca.router, prefix="/seguranca", tags=["segurança"])


@app.get("/health", tags=["status"])
def health_check():
    return {"status": "ok", "modo_simulacao": settings.MODO_SIMULACAO}


async def _loop_simulacao_sensores():
    while True:
        await asyncio.sleep(15)
        simular_nova_leitura()


async def _loop_monitoramento():
    """Each tick: copy the latest reading from Orion, then check alert conditions.
    Conditions are checked even when Orion fails, since that is exactly when
    the sensor stops communicating. Orion problems are logged only on state
    changes, so an outage produces one warning instead of one every poll."""
    niveis = await asyncio.to_thread(niveis_salvos, persistencia.obter_repositorio())
    monitor = MonitorDeAlertas(monitorando_desde=datetime.now(), niveis=niveis)
    estado_anterior = None
    async with httpx.AsyncClient(base_url=settings.FIWARE_URL, timeout=5) as client:
        while True:
            try:
                estado = "ok" if await sincronizar_ar_condicionado(client) else "sem_leitura"
                detalhe = ""
            except (httpx.HTTPError, ValidationError) as e:
                estado, detalhe = "erro", f"{type(e).__name__}: {e}"
            if estado != estado_anterior:
                if estado == "ok":
                    log.info("FIWARE: recebendo leituras do ar-condicionado")
                elif estado == "sem_leitura":
                    log.warning("FIWARE: aguardando o sensor publicar %s", settings.FIWARE_ENTIDADE_AR_CONDICIONADO)
                else:
                    log.warning("FIWARE: falha ao ler o Orion em %s (%s)", settings.FIWARE_URL, detalhe)
                estado_anterior = estado

            try:
                for alerta in await monitor.verificar(LEITURA_ATUAL, datetime.now()):
                    log.info("Alerta gerado: %s", alerta["titulo"])
                LEITURA_ATUAL.update(estado_para_o_app(monitor.niveis))
            except Exception:
                # A bug in one check must not silently stop all monitoring.
                log.exception("Falha ao verificar as condições de alerta")

            try:
                await _atualizar_historico(estado == "ok")
            except Exception:
                log.exception("Falha ao gravar o histórico de médias")

            await asyncio.sleep(settings.FIWARE_INTERVALO_S)


async def _atualizar_historico(leitura_recebida: bool):
    """Feeds the current reading to the averages and stores every closed period."""
    fechados = []
    medido_em = LEITURA_ATUAL["temperatura_atualizada_em"]
    if leitura_recebida and medido_em:
        fechados += _agregador.adicionar(
            datetime.fromisoformat(medido_em), LEITURA_ATUAL["temperatura_c"], LEITURA_ATUAL["umidade_pct"]
        )
    fechados += _agregador.fechar_vencidos(datetime.now())
    for media in fechados:
        await asyncio.to_thread(persistencia.obter_repositorio().salvar_media, media)
        log.info("Média gravada: %s, %d leituras", media.inicio.strftime("%d/%m %H:%M"), media.amostras)


def _iniciar_em_background(corrotina):
    tarefa = asyncio.create_task(corrotina)
    _tarefas_em_background.add(tarefa)
    tarefa.add_done_callback(_tarefas_em_background.discard)


@app.on_event("startup")
async def iniciar_tarefas_em_background():
    # Without the database the history would be silently lost, so the backend
    # refuses to start instead. The tests configure their own storage first.
    if not persistencia.configurado():
        persistencia.configurar(await asyncio.to_thread(persistencia.criar_repositorio))
        log.info("Armazenamento: %s", settings.ARMAZENAMENTO)
    _iniciar_em_background(_loop_monitoramento())
    if settings.MODO_SIMULACAO:
        _iniciar_em_background(_loop_simulacao_sensores())


@app.on_event("shutdown")
async def encerrar():
    if not persistencia.configurado():
        return  # startup failed before connecting, so there is nothing to save
    # The partial average of the current period is stored now and merged with
    # the rest of the period after the next start.
    repositorio = persistencia.obter_repositorio()
    for media in _agregador.esvaziar():
        await asyncio.to_thread(repositorio.salvar_media, media)
    await asyncio.to_thread(repositorio.fechar)
