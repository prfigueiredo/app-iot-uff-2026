"""
App de Monitoramento do CPD - STI Niterói-RJ
Ponto de entrada da API backend (FastAPI).
"""
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.mock_db import simular_nova_leitura
from app.core.ws_manager import ws_manager
from app.api import auth, sensores, alertas, integracoes, dashboard, seguranca

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


@app.on_event("startup")
async def iniciar_simulacao():
    if settings.MODO_SIMULACAO:
        asyncio.create_task(_loop_simulacao_sensores())
