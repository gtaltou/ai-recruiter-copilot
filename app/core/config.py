from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AI Recruiter Copilot"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    OPENAI_API_KEY: str = ""
    JWT_SECRET: str = "test-secret-key-which-is-32-chars-long!"
    JWT_ALGORITHM: str = "HS256"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    WEBHOOK_URL: str = ""
    NOTIFY_EMAIL_TO: str = ""



    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
