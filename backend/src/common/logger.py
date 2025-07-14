import logging
import os


class Logger:

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            sh = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            sh.setFormatter(formatter)
            self._logger.addHandler(sh)

    def debug(self, msg):
        self._logger.debug(msg)

    def trace(self, msg):
        self._logger.info(msg)

    def info(self, msg):
        self._logger.info(msg)

    def warn(self, msg):
        self._logger.warning(msg)

    def error(self, msg, e=None):
        if e:
            self._logger.error(f"{msg}: {e}")
        else:
            self._logger.error(msg)


def get_logger(name="app"):
    return Logger(name)
