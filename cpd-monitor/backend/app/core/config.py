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

    # Shared key the air conditioning sensor sends in the X-Sensor-Key header.
    SENSOR_API_KEY: str = os.getenv("SENSOR_API_KEY", "chave-sensor-dev")

    # Above this temperature the heat sensor flags an alert.
    LIMITE_TEMPERATURA_C: float = float(os.getenv("LIMITE_TEMPERATURA_C", "28"))

    # Endpoints reais (usados quando MODO_SIMULACAO = false)
    GRAYLOG_URL: str = os.getenv("GRAYLOG_URL", "")
    GRAYLOG_TOKEN: str = os.getenv("GRAYLOG_TOKEN", "")
    ZABBIX_URL: str = os.getenv("ZABBIX_URL", "")
    ZABBIX_TOKEN: str = os.getenv("ZABBIX_TOKEN", "")


settings = Settings()
