from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    entorno: str = "desarrollo"
    zona_horaria_local: str = "America/Mexico_City"

    database_url: str = "postgresql+asyncpg://rondines:rondines@postgres:5432/rondines"

    hikconnect_app_key: SecretStr | None = None
    hikconnect_secret_key: SecretStr | None = None

    umbral_default_minutos: int = 45
    escalamiento_supervisor_minutos: int = 15
    escalamiento_gerencia_minutos: int = 30
    intervalo_vigilante_segundos: int = 60
    intervalo_polling_segundos: int = 1

    telegram_bot_token: SecretStr | None = None
    telegram_chat_id_operativo: str | None = None
    telegram_chat_id_escalamiento: str | None = None

    outbox_max_intentos: int = 5
    outbox_backoff_base_segundos: int = 10

settings = Settings()   