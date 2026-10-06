"""
Configurações centrais do backend.
Lê variáveis de ambiente com valores padrão seguros para desenvolvimento local.
"""
import os


class Settings:
    # Banco de dados (PostgreSQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://cpd_user:cpd_pass@localhost:5432/cpd_monitor",
    )

    # Segurança / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Modo simulação: enquanto não há acesso real ao GrayLog/Zabbix/sensores do CPD,
    # os serviços em app/services/ retornam dados simulados em vez de chamar as APIs reais.
    MODO_SIMULACAO: bool = os.getenv("MODO_SIMULACAO", "true").lower() == "true"

    # FIWARE Orion Context Broker (NGSI-v2). Sensors publish there and the backend
    # reads from there, so a new sensor never needs a new backend endpoint.
    FIWARE_URL: str = os.getenv("FIWARE_URL", "http://127.0.0.1:1026")
    FIWARE_ENTIDADE_AR_CONDICIONADO: str = os.getenv(
        "FIWARE_ENTIDADE_AR_CONDICIONADO", "urn:ngsi-ld:ArCondicionado:cpd-01"
    )
    FIWARE_INTERVALO_S: float = float(os.getenv("FIWARE_INTERVALO_S", "2"))

    # Above this temperature the heat sensor flags an alert.
    LIMITE_TEMPERATURA_C: float = float(os.getenv("LIMITE_TEMPERATURA_C", "28"))

    # Endpoints reais (usados quando MODO_SIMULACAO = false)
    GRAYLOG_URL: str = os.getenv("GRAYLOG_URL", "")
    GRAYLOG_TOKEN: str = os.getenv("GRAYLOG_TOKEN", "")
    ZABBIX_URL: str = os.getenv("ZABBIX_URL", "")
    ZABBIX_TOKEN: str = os.getenv("ZABBIX_TOKEN", "")


settings = Settings()
