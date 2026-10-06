"""
Alert generation (V2). An alert is created when a condition changes level,
never once per reading, so a sustained problem produces one alert, not spam.
"""
from datetime import datetime

from app.core.config import settings
from app.core.mock_db import ALERTAS, proximo_id_alerta
from app.core.ws_manager import ws_manager
from app.services.regras_alerta import (
    AR_DESLIGADO,
    CONDICOES,
    SEM_COMUNICACAO,
    TEMPERATURA,
    UMIDADE,
    Nivel,
    avaliar,
)


async def registrar_alerta(
    titulo: str, descricao: str, severidade: str, canal: str = "push", condicao: str | None = None
) -> dict:
    """The only way alerts are created: stores the alert and pushes it to the app."""
    alerta = {
        "id": proximo_id_alerta(),
        "titulo": titulo,
        "descricao": descricao,
        "severidade": severidade,
        "canal": canal,
        "condicao": condicao,
        "data": datetime.now().isoformat(),
        "lido": False,
    }
    ALERTAS.insert(0, alerta)
    await ws_manager.transmitir({"tipo": "novo_alerta", "alerta": alerta})
    return alerta


def conteudo_do_alerta(condicao: str, anterior: Nivel, novo: Nivel, leitura: dict) -> tuple[str, str, str] | None:
    """Returns (titulo, descricao, severidade) for a level change, or None when
    the change does not deserve an alert (same level, or improved but not normal)."""
    if novo > anterior:
        return _alerta_de_problema(condicao, novo, leitura)
    if novo == Nivel.NORMAL and anterior > Nivel.NORMAL:
        return _alerta_de_normalizacao(condicao, leitura)
    return None


def _alerta_de_problema(condicao: str, nivel: Nivel, leitura: dict) -> tuple[str, str, str]:
    critico = nivel == Nivel.CRITICO
    severidade = "alta" if critico else "media"
    if condicao == TEMPERATURA:
        limite = settings.LIMITE_TEMPERATURA_C if critico else settings.TEMPERATURA_ATENCAO_C
        titulo = "Temperatura crítica" if critico else "Temperatura em atenção"
        return titulo, f"O ar-condicionado registrou {leitura['temperatura_c']:.1f}°C, acima de {limite:g}°C.", severidade
    if condicao == UMIDADE:
        limite = settings.UMIDADE_CRITICA_PCT if critico else settings.UMIDADE_ATENCAO_PCT
        titulo = "Umidade crítica" if critico else "Umidade elevada"
        return (
            titulo,
            f"Umidade em {leitura['umidade_pct']:.0f}% perto do ar-condicionado, acima de {limite:g}%. "
            "Verifique se há vazamento de água.",
            severidade,
        )
    if condicao == AR_DESLIGADO:
        return "Ar-condicionado desligado", "O sensor informou que o ar-condicionado do CPD está desligado.", severidade
    if condicao == SEM_COMUNICACAO:
        return (
            "Sensor sem comunicação",
            f"Nenhuma leitura do ar-condicionado há mais de {settings.SENSOR_SEM_COMUNICACAO_S:g}s. "
            "Os valores exibidos podem estar desatualizados.",
            severidade,
        )
    raise ValueError(f"condição desconhecida: {condicao}")


def _alerta_de_normalizacao(condicao: str, leitura: dict) -> tuple[str, str, str]:
    if condicao == TEMPERATURA:
        return "Temperatura normalizada", f"A temperatura voltou para {leitura['temperatura_c']:.1f}°C.", "baixa"
    if condicao == UMIDADE:
        return "Umidade normalizada", f"A umidade voltou para {leitura['umidade_pct']:.0f}%.", "baixa"
    if condicao == AR_DESLIGADO:
        return "Ar-condicionado religado", "O sensor informou que o ar-condicionado voltou a funcionar.", "baixa"
    if condicao == SEM_COMUNICACAO:
        return "Sensor voltou a comunicar", "O sensor do ar-condicionado voltou a enviar leituras.", "baixa"
    raise ValueError(f"condição desconhecida: {condicao}")


def estado_para_o_app(niveis: dict[str, Nivel]) -> dict:
    """Fields the app shows next to the readings. Derived from the same levels
    that generate alerts, so a card never says "normal" while an alert is open."""
    return {
        "niveis_alerta": {condicao: nivel.name.lower() for condicao, nivel in niveis.items()},
        "sensor_calor_alerta": niveis[TEMPERATURA] == Nivel.CRITICO,
    }


class MonitorDeAlertas:
    """Remembers the current level of each condition and alerts on changes."""

    def __init__(self, monitorando_desde: datetime):
        self.monitorando_desde = monitorando_desde
        self.niveis = {condicao: Nivel.NORMAL for condicao in CONDICOES}

    async def verificar(self, leitura: dict, agora: datetime) -> list[dict]:
        novos = avaliar(leitura, self.niveis, agora, self.monitorando_desde)
        gerados = []
        for condicao in CONDICOES:
            conteudo = conteudo_do_alerta(condicao, self.niveis[condicao], novos[condicao], leitura)
            if conteudo:
                titulo, descricao, severidade = conteudo
                gerados.append(await registrar_alerta(titulo, descricao, severidade, condicao=condicao))
        self.niveis = novos
        return gerados
