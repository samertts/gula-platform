import logging
import sys
from typing import Any


class LogManager:
    def __init__(self):
        self._loggers: dict[str, logging.Logger] = {}

    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]

    def set_level(self, name: str, level: str | int) -> None:
        logger = self.get_logger(name)
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level)

    def set_global_level(self, level: str | int) -> None:
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(level)

    def add_console_handler(self, name: str, level: str | int | None = None) -> None:
        logger = self.get_logger(name)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        if level:
            if isinstance(level, str):
                level = getattr(logging, level.upper(), logging.INFO)
            handler.setLevel(level)
        logger.addHandler(handler)

    def add_file_handler(self, name: str, filepath: str, level: str | int | None = None) -> None:
        logger = self.get_logger(name)
        handler = logging.FileHandler(filepath)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        if level:
            if isinstance(level, str):
                level = getattr(logging, level.upper(), logging.INFO)
            handler.setLevel(level)
        logger.addHandler(handler)

    def get_logger_names(self) -> list[str]:
        return list(self._loggers.keys())

    def get_logger_config(self) -> dict[str, Any]:
        config = {}
        for name, logger in self._loggers.items():
            config[name] = {
                "level": logging.getLevelName(logger.level),
                "handlers": len(logger.handlers),
                "propagate": logger.propagate,
            }
        return config
