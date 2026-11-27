from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://rankforge:rankforge_dev_password@localhost:5432/rankforge"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:19092"
    kafka_catalog_topic: str = "catalog.events"
    kafka_dlq_topic: str = "catalog.dlq"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
