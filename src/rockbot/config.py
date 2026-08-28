from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Rocket.Chat REST API base URL (no websockets involved).
    rocketchat_url: str = "http://localhost:3000"
    rocketchat_user_id: str
    rocketchat_token: str

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_system_prompt: str = (
        "You are a helpful assistant answering questions in a Rocket.Chat channel."
    )

    # Bot behaviour
    rockbot_trigger: str = "/rockbot"
    rockbot_poll_interval: float = 2.0
    rockbot_history_length: int = 10
    rockbot_log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()
