from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Facebook
    fb_verify_token: str
    fb_page_access_token: str
    fb_graph_api_version: str = "v21.0"

    # AI Provider: "openai" | "gemini" | "ollama"
    ai_provider: str = "ollama"
    ai_model: str = "llama3.2"
    ai_timeout: int = 30
    ai_system_prompt: str = (
        "Bạn là trợ lý ảo của Luniva Studio. "
        "Trả lời ngắn gọn, thân thiện, bằng tiếng Việt."
    )

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # Gemini
    gemini_api_key: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Logging
    log_level: str = "INFO"

    @property
    def fb_messages_url(self) -> str:
        return f"https://graph.facebook.com/{self.fb_graph_api_version}/me/messages"


settings = Settings()
