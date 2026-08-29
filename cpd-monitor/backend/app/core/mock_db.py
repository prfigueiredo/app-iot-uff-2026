"""
Base de dados MOCKADA em memória.

Enquanto não há acesso real ao ambiente do CPD (GrayLog, Zabbix, sensores),
todo o estado da aplicação vive aqui em estruturas Python simples. Isso deixa
o app 100% testável sem exigir instalação de PostgreSQL ou acesso à rede do
CPD. Quando o acesso real estiver disponível, esse módulo é substituído por
uma camada real de banco de dados sem que as rotas precisem mudar de formato
de resposta.
"""
import random
from datetime import datetime, timedelta

from app.core.security import hash_senha

# ---------------------------------------------------------------------------
# Usuários e perfis de acesso
# ---------------------------------------------------------------------------
USUARIOS = [
    {
        "id": 1,
        "usuario": "admin",
        "nome": "Administrador STI",
        "senha_hash": hash_senha("admin123"),
        "perfil": "admin",
    },
    {
        "id": 2,
        "usuario": "operador",
        "nome": "Operador de Plantão",
        "senha_hash": hash_senha("operador123"),
        "perfil": "operador",
    },
    {
        "id": 3,
        "usuario": "visualizador",
        "nome": "Usuário Visualizador",
        "senha_hash": hash_senha("visual123"),
        "perfil": "visualizador",
    },
]

TENTATIVAS_ACESSO_INDEVIDO = []


def registrar_tentativa_indevida(usuario: str, motivo: str):
    TENTATIVAS_ACESSO_INDEVIDO.append(
        {"usuario": usuario, "motivo": motivo, "data": datetime.now().isoformat()}
    )


# ---------------------------------------------------------------------------
# Sensores físicos do CPD
# ---------------------------------------------------------------------------
LEITURA_ATUAL = {
    "temperatura_c": 21.5,
    "umidade_pct": 48.0,
    "combustivel_gerador_pct": 82.0,
    "pessoas_presentes": 1,
    "sensor_presenca_ativo": True,
    "sensor_calor_alerta": False,
    "ar_condicionado_status": "ligado",
    "atualizado_em": datetime.now().isoformat(),
}

HISTORICO_SENSORES = []


def _seed_historico_sensores():
    agora = datetime.now()
    for i in range(48, 0, -1):
        momento = agora - timedelta(minutes=30 * i)
        HISTORICO_SENSORES.append(
            {
                "temperatura_c": round(20 + random.uniform(-1.5, 3.5), 1),
                "umidade_pct": round(45 + random.uniform(-5, 10), 1),
                "combustivel_gerador_pct": round(82 + random.uniform(-0.5, 0.5), 1),
                "pessoas_presentes": random.choice([0, 0, 0, 1, 1, 2]),
                "atualizado_em": momento.isoformat(),
            }
        )


_seed_historico_sensores()


def simular_nova_leitura():
    LEITURA_ATUAL["temperatura_c"] = round(
        max(16, min(32, LEITURA_ATUAL["temperatura_c"] + random.uniform(-0.4, 0.4))), 1
    )
    LEITURA_ATUAL["umidade_pct"] = round(
        max(20, min(80, LEITURA_ATUAL["umidade_pct"] + random.uniform(-1, 1))), 1
    )
    LEITURA_ATUAL["combustivel_gerador_pct"] = round(
        max(0, LEITURA_ATUAL["combustivel_gerador_pct"] - random.uniform(0, 0.05)), 1
    )
    LEITURA_ATUAL["sensor_calor_alerta"] = LEITURA_ATUAL["temperatura_c"] > 28
    LEITURA_ATUAL["atualizado_em"] = datetime.now().isoformat()

    HISTORICO_SENSORES.append({**LEITURA_ATUAL})
    if len(HISTORICO_SENSORES) > 200:
        HISTORICO_SENSORES.pop(0)

    return LEITURA_ATUAL


# ---------------------------------------------------------------------------
# GrayLog (mock)
# ---------------------------------------------------------------------------
_NIVEIS_LOG = ["INFO", "WARNING", "ERROR", "CRITICAL"]
_ORIGENS_LOG = ["srv-app-01", "srv-db-01", "srv-web-02", "firewall-cpd", "srv-backup-01"]
_MENSAGENS_LOG = [
    "Serviço reiniciado com sucesso",
    "Uso de CPU acima de 85%",
    "Falha ao conectar no banco de dados",
    "Backup diário concluído",
    "Tentativa de login SSH bloqueada",
    "Espaço em disco abaixo de 10%",
    "Certificado SSL expira em 7 dias",
]

LOGS_GRAYLOG = [
    {
        "id": i,
        "nivel": random.choice(_NIVEIS_LOG),
        "origem": random.choice(_ORIGENS_LOG),
        "mensagem": random.choice(_MENSAGENS_LOG),
        "data": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
    }
    for i in range(1, 41)
]
LOGS_GRAYLOG.sort(key=lambda x: x["data"], reverse=True)

# ---------------------------------------------------------------------------
# Zabbix (mock)
# ---------------------------------------------------------------------------
SERVICOS_ZABBIX = [
    {"id": 1, "nome": "srv-app-01", "tipo": "Servidor de Aplicação", "status": "up", "uptime_pct": 99.98},
    {"id": 2, "nome": "srv-db-01", "tipo": "Banco de Dados", "status": "up", "uptime_pct": 99.95},
    {"id": 3, "nome": "srv-web-02", "tipo": "Servidor Web", "status": "up", "uptime_pct": 99.90},
    {"id": 4, "nome": "firewall-cpd", "tipo": "Rede", "status": "warning", "uptime_pct": 98.70},
    {"id": 5, "nome": "srv-backup-01", "tipo": "Backup", "status": "down", "uptime_pct": 95.10},
]

# ---------------------------------------------------------------------------
# Alertas e perfis de alerta personalizados
# ---------------------------------------------------------------------------
ALERTAS = [
    {
        "id": 1,
        "titulo": "Backup falhou",
        "descricao": "srv-backup-01 está fora do ar há 12 minutos",
        "severidade": "alta",
        "canal": "push",
        "data": (datetime.now() - timedelta(minutes=12)).isoformat(),
        "lido": False,
    },
    {
        "id": 2,
        "titulo": "Firewall com instabilidade",
        "descricao": "firewall-cpd apresentou 3 quedas de pacote nos últimos 5 minutos",
        "severidade": "media",
        "canal": "email",
        "data": (datetime.now() - timedelta(hours=1)).isoformat(),
        "lido": False,
    },
]

PERFIS_ALERTA = [
    {
        "id": 1,
        "nome": "Horário comercial",
        "periodo": "seg-sex 08:00-18:00",
        "canais": ["push", "email"],
        "equipe": "Suporte N1",
        "ativo": True,
    },
    {
        "id": 2,
        "nome": "Plantão fins de semana e feriados",
        "periodo": "sáb-dom e feriados, 24h",
        "canais": ["sms", "push"],
        "equipe": "Plantão de Infraestrutura",
        "ativo": True,
    },
]

_prox_id_perfil_alerta = 3


def proximo_id_perfil_alerta():
    global _prox_id_perfil_alerta
    valor = _prox_id_perfil_alerta
    _prox_id_perfil_alerta += 1
    return valor


# ---------------------------------------------------------------------------
# Preferências de dashboard por usuário
# ---------------------------------------------------------------------------
PREFERENCIAS_DASHBOARD = {
    1: {"metricas": ["temperatura", "umidade", "combustivel", "presenca"], "servicos": ["srv-app-01", "srv-db-01"], "tipos_alerta": ["alta", "media"]},
    2: {"metricas": ["temperatura", "combustivel"], "servicos": ["srv-backup-01"], "tipos_alerta": ["alta"]},
    3: {"metricas": ["temperatura", "umidade"], "servicos": [], "tipos_alerta": ["alta", "media", "baixa"]},
}
