"""
Alertas (SMS, e-mail, push) e perfis de alerta personalizados.
"""
import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.mock_db import ALERTAS, PERFIS_ALERTA, proximo_id_perfil_alerta, registrar_tentativa_indevida
from app.core.security import decodificar_token
from app.core.ws_manager import ws_manager
from app.services.alertas import registrar_alerta

router = APIRouter()

TEMPO_PARA_AUTENTICAR_S = 5


@router.get("")
def listar_alertas(usuario: dict = Depends(get_usuario_atual)):
    return ALERTAS


@router.post("/{alerta_id}/lido")
def marcar_alerta_lido(alerta_id: int, usuario: dict = Depends(get_usuario_atual)):
    """Marca um alerta como lido (o estado de leitura é compartilhado entre usuários)."""
    alerta = next((a for a in ALERTAS if a["id"] == alerta_id), None)
    if alerta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta não encontrado")
    alerta["lido"] = True
    return alerta


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
    titulo: str = Field(min_length=1)
    descricao: str = Field(min_length=1)
    severidade: Literal["alta", "media", "baixa"] = "media"
    canal: Literal["sms", "email", "push"] = "push"


@router.post("/simular")
async def simular_alerta(dados: AlertaSimulado, usuario: dict = Depends(exigir_perfil("admin", "operador"))):
    """Dispara um alerta simulado (útil para testar notificações push em tempo real)."""
    return await registrar_alerta(dados.titulo, dados.descricao, dados.severidade, dados.canal)


@router.websocket("/ws")
async def alertas_websocket(websocket: WebSocket):
    """Canal de push notification em tempo real para o app Flutter.
    A primeira mensagem deve ser {"token": "<token de login>"}. O servidor responde
    {"tipo": "autenticado"} e depois envia {"tipo": "novo_alerta", "alerta": {...}}."""
    # The token travels as the first message, not in the URL, because URLs
    # end up in access logs and browsers cannot set headers on a WebSocket.
    await websocket.accept()
    try:
        mensagem = await asyncio.wait_for(websocket.receive_json(), timeout=TEMPO_PARA_AUTENTICAR_S)
        token = mensagem.get("token", "") if isinstance(mensagem, dict) else ""
    except WebSocketDisconnect:
        return
    except (asyncio.TimeoutError, ValueError, KeyError):
        # Timeout, invalid JSON, or a binary frame instead of text.
        token = ""
    if not token or decodificar_token(token) is None:
        registrar_tentativa_indevida("desconhecido", "WebSocket de alertas sem token válido")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    ws_manager.adicionar(websocket)
    # Tells the client it is subscribed, so it knows no alert can be missed from now on.
    await websocket.send_json({"tipo": "autenticado"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.desconectar(websocket)
