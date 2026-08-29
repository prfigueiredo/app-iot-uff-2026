"""
Alertas (SMS, e-mail, push) e perfis de alerta personalizados.
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.mock_db import ALERTAS, PERFIS_ALERTA, proximo_id_perfil_alerta
from app.core.ws_manager import ws_manager
from datetime import datetime

router = APIRouter()


@router.get("")
def listar_alertas(usuario: dict = Depends(get_usuario_atual)):
    return ALERTAS


@router.get("/perfis")
def listar_perfis_alerta(usuario: dict = Depends(get_usuario_atual)):
    return PERFIS_ALERTA


class PerfilAlertaEntrada(BaseModel):
    nome: str
    periodo: str
    canais: list[str]
    equipe: str
    ativo: bool = True


@router.post("/perfis")
def criar_perfil_alerta(dados: PerfilAlertaEntrada, usuario: dict = Depends(exigir_perfil("admin", "operador"))):
    """Cria um perfil de alerta personalizado. Restrito a admin/operador."""
    novo = {"id": proximo_id_perfil_alerta(), **dados.model_dump()}
    PERFIS_ALERTA.append(novo)
    return novo


class AlertaSimulado(BaseModel):
    titulo: str
    descricao: str
    severidade: str = "media"
    canal: str = "push"


@router.post("/simular")
async def simular_alerta(dados: AlertaSimulado, usuario: dict = Depends(exigir_perfil("admin", "operador"))):
    """Dispara um alerta simulado (útil para testar notificações push em tempo real)."""
    novo = {
        "id": max((a["id"] for a in ALERTAS), default=0) + 1,
        **dados.model_dump(),
        "data": datetime.now().isoformat(),
        "lido": False,
    }
    ALERTAS.insert(0, novo)
    await ws_manager.transmitir({"tipo": "novo_alerta", "alerta": novo})
    return novo


@router.websocket("/ws")
async def alertas_websocket(websocket: WebSocket):
    """Canal de push notification em tempo real para o app Flutter."""
    await ws_manager.conectar(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.desconectar(websocket)
