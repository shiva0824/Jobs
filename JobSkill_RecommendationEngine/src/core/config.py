from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # -------------------------------
    # Database
    # -------------------------------
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str

    # -------------------------------
    # S3 and AWS
    # -------------------------------
    S3_BUCKET: str
    S3_MODEL_PREFIX: str
    S3_DICT_KEY: str
    AWS_DEFAULT_REGION: str

    # -------------------------------
    # App Environment
    # -------------------------------
    ENV: str = "production"
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()