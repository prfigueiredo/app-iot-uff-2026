"""
Gerenciador simples de conexões WebSocket, usado para simular push
notifications de alertas em tempo real dentro do próprio app.
"""
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.conexoes_ativas: list[WebSocket] = []

    async def conectar(self, websocket: WebSocket):
        await websocket.accept()
        self.conexoes_ativas.append(websocket)

    def desconectar(self, websocket: WebSocket):
        if websocket in self.conexoes_ativas:
            self.conexoes_ativas.remove(websocket)

    async def transmitir(self, mensagem: dict):
        mortas = []
        for conexao in self.conexoes_ativas:
            try:
                await conexao.send_json(mensagem)
            except Exception:
                mortas.append(conexao)
        for conexao in mortas:
            self.desconectar(conexao)


ws_manager = WebSocketManager()
