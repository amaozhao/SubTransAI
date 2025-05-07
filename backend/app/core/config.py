from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SubTransAI"
    
    # 文件存储路径
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "data/uploads"
    CHUNKS_DIR: str = "data/chunks"
    RESULTS_DIR: str = "data/results"
    
    # 下载 URL 配置
    DOWNLOAD_BASE_URL: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            path=f"{values.data.get('POSTGRES_DB') or ''}",
        )
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # API Rate Limiting
    RATE_LIMIT_PER_SECOND: int = 50
    
    # DeepSeek API
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_URL: Optional[str] = None
    
    # Mistral API
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_API_URL: Optional[str] = None
    
    # 智能体配置
    AGNO_CHUNK_SIZE: int = 100  # 每个块的最大字幕数量
    AGNO_DEFAULT_ENGINE: str = "mistral"  # 默认翻译引擎
    AGNO_URL_EXPIRY_HOURS: int = 24  # 下载 URL 过期时间（小时）
    AGNO_MAX_RETRIES: int = 3  # 最大重试次数
    AGNO_RETRY_DELAY: int = 5  # 重试延迟（秒）
    
    # 各智能体模型配置
    AGNO_VALIDATOR_ENGINE: str = "mistral"  # SRT 校验智能体使用的模型
    AGNO_SPLITTER_ENGINE: str = "mistral"   # SRT 分块智能体使用的模型
    AGNO_TRANSLATOR_ENGINE: str = "mistral" # 翻译智能体使用的模型
    AGNO_REASSEMBLER_ENGINE: str = "mistral" # SRT 重组智能体使用的模型
    AGNO_NOTIFICATION_ENGINE: str = "mistral" # 通知智能体使用的模型
    
    # Sensitive Words
    # SENSITIVE_WORDS_OSS_URL: Optional[str] = None
    # SENSITIVE_WORDS_UPDATE_INTERVAL: int = 3600  # 1 hour in seconds


settings = Settings()
