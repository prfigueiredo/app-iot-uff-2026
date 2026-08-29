"""
Integrações com GrayLog (logs) e Zabbix (monitoramento de infraestrutura).
Em MODO_SIMULACAO, retornam dados mockados de app/core/mock_db.py.
"""
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.deps import get_usuario_atual
from app.core.mock_db import LOGS_GRAYLOG, SERVICOS_ZABBIX

router = APIRouter()


@router.get("/graylog/logs")
def logs_graylog(nivel: str | None = None, limite: int = 50, usuario: dict = Depends(get_usuario_atual)):
    """Logs de uso dos servidores do CPD via GrayLog."""
    logs = LOGS_GRAYLOG
    if nivel:
        logs = [l for l in logs if l["nivel"].lower() == nivel.lower()]
    return {"modo_simulacao": settings.MODO_SIMULACAO, "logs": logs[:limite]}


@router.get("/zabbix/status")
def status_zabbix(usuario: dict = Depends(get_usuario_atual)):
    """Status dos serviços/hosts monitorados pelo Zabbix."""
    return {"modo_simulacao": settings.MODO_SIMULACAO, "servicos": SERVICOS_ZABBIX}
