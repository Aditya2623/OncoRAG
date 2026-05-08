from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "OncoRag"
    APP_ENV: str = "development"

    # Redis

    # Qdrant
    BASE_URL: str = "http://localhost:6333"
    COLLECTION_NAME: str = "pubmed-oncorag"

    # PUBMED
    PUBMED_EMAIL: str

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
