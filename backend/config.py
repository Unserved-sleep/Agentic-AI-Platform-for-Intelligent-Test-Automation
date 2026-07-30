import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    project_name: str = "Intelligent Test Automation Platform"
    
    # PostgreSQL Database
    postgres_user: str = "postgres"
    postgres_password: str = "Sandy168$"
    postgres_server: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "agentic_test_db"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
    
    # Qdrant Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Groq API configuration
    groq_api_key: str = os.getenv("GROQ_API_KEY")

    class Config:
        env_file = "../.env"

settings = Settings()
