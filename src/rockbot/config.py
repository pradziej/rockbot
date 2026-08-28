from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Rocket.Chat REST API base URL (no websockets involved).
    rocketchat_url: str = "http://localhost:3000"
    rocketchat_user_id: str
    rocketchat_token: str
    # Set to false to skip TLS certificate verification, e.g. when the
    # server uses a self-signed certificate. Only use this for a trusted
    # instance - it removes protection against man-in-the-middle attacks.
    rocketchat_verify_ssl: bool = True

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_system_prompt: str = (
        "You are a helpful assistant answering questions in a Rocket.Chat channel."
    )

    # Bot behaviour
    rockbot_trigger: str = "/rockbot"
    rockbot_poll_interval: float = 2.0
    # Comma-separated room IDs and/or names (channel/group name, or DM
    # counterpart's username) to restrict polling to. Empty means "every
    # room the bot is a member of".
    rockbot_rooms: str = ""
    rockbot_history_length: int = 10
    rockbot_log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()
