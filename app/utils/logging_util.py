import logging
from pydantic_settings import BaseSettings

class LogConfig(BaseSettings):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "my_app"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(name)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    # Define the logging configuration dictionary
    def get_dict_config(self):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": self.LOG_FORMAT,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                self.LOGGER_NAME: {"handlers": ["default"], "level": self.LOG_LEVEL},
            },
        }