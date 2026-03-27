from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8383

    fb_verify_token: str
    fb_page_access_token: str
    fb_graph_api_version: str = "v21.0"

    gemini_api_key: str
    gemini_model: str = "gemma-3-27b-it"
    ai_timeout: int = 30
    ai_system_prompt: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    database_path: str = "data/conversations.db"
    vector_db_path: str = "data/vectordb"

    log_level: str = "INFO"

    @property
    def fb_messages_url(self) -> str:
        return f"https://graph.facebook.com/{self.fb_graph_api_version}/me/messages"


settings = Settings()
