from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Rocket.Chat
    rocketchat_url: str = "ws://localhost:3000/websocket"
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
    rockbot_history_length: int = 10
    rockbot_log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()
