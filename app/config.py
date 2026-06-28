from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Address Book API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./addresses.db"
    
    # Allows setting variables via environment or .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
