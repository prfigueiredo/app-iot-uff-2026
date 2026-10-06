"""
App de Monitoramento do CPD - STI Niterói-RJ
Ponto de entrada da API backend (FastAPI).
"""
import asyncio
import logging

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.core.config import settings
from app.core.mock_db import simular_nova_leitura
from app.core.ws_manager import ws_manager
from app.api import auth, sensores, alertas, integracoes, dashboard, seguranca
from app.services.fiware import sincronizar_ar_condicionado

log = logging.getLogger("uvicorn.error")

# asyncio keeps only weak references to tasks, so background loops are held here.
_tarefas_em_background: set[asyncio.Task] = set()

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
app.include_router(integracoes.router, prefix="/integracoes", tags=["graylog/zabbix"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(seguranca.router, prefix="/seguranca", tags=["segurança"])


@app.get("/health", tags=["status"])
def health_check():
    return {"status": "ok", "modo_simulacao": settings.MODO_SIMULACAO}


async def _loop_simulacao_sensores():
    while True:
        await asyncio.sleep(15)
        leitura = simular_nova_leitura()
        if leitura["sensor_calor_alerta"]:
            await ws_manager.transmitir(
                {
                    "tipo": "novo_alerta",
                    "alerta": {
                        "titulo": "Temperatura acima do limite",
                        "descricao": f"Sensor de calor detectou {leitura['temperatura_c']}°C no CPD",
                        "severidade": "alta",
                        "canal": "push",
                    },
                }
            )


async def _loop_fiware():
    """Polls Orion for the air conditioning reading. Logs only state changes,
    so an Orion outage produces one warning instead of one every poll."""
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
            await asyncio.sleep(settings.FIWARE_INTERVALO_S)


def _iniciar_em_background(corrotina):
    tarefa = asyncio.create_task(corrotina)
    _tarefas_em_background.add(tarefa)
    tarefa.add_done_callback(_tarefas_em_background.discard)


@app.on_event("startup")
async def iniciar_tarefas_em_background():
    _iniciar_em_background(_loop_fiware())
    if settings.MODO_SIMULACAO:
        _iniciar_em_background(_loop_simulacao_sensores())
