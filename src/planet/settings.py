from enum import Enum
from logging import basicConfig

from pydantic_settings import BaseSettings

ENV = "staging"
API_DOMAINS = {
    "production": "https://api.planet.com",
    "staging": "https://api.staging.planet-labs.com",
}
API_DOMAIN = API_DOMAINS[ENV]


class LogLevel(Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class Settings(BaseSettings):
    loglevel: LogLevel = LogLevel.DEBUG
    api_domain: str = API_DOMAIN
    api_base_url: str = API_DOMAIN + "/tasking/v2"
    env: str = ENV

    @classmethod
    def load(cls) -> "Settings":
        settings = Settings()
        basicConfig(level=settings.loglevel.value)
        return settings
