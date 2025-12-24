# app/logger.py
import logging
from logging.config import dictConfig
from pydantic_settings import BaseSettings

class LogConfig(BaseSettings):
    """Logging configuration to be set for the server"""
    LOGGER_NAME: str = "sql_engine" # Renamed for clarity
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(name)s | %(message)s"
    LOG_LEVEL: str = "INFO"

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

def setup_logger():
    """Initializes the logging configuration and returns the logger instance."""
    config = LogConfig()
    dictConfig(config.get_dict_config())
    return logging.getLogger(config.LOGGER_NAME)

# Create a singleton logger instance to be imported elsewhere
logger = setup_logger()