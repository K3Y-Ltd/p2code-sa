from typing import Any, Dict
import logging
import threading


class Logger:
    """
    Singleton class to manage logging configuration.
    """

    _instance = None
    _lock = threading.Lock()
    _logger = None
    # _step_counter = 0

    def __new__(cls) -> "Logger":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def setup_logging(self, config: Dict[str, Any]) -> None:
        """
        Setup logging configuration.

        Args:
            config: The logging configuration.
        """
        logging.basicConfig(level=config["root"]["level"])
        self._logger = logging.getLogger(__name__)
        self._logger.info("Logging configured")

    def get_logger(self) -> logging.Logger:
        """
        Get the logger instance.

        Returns:
            The logger instance.
        """
        if self._logger is None:
            raise RuntimeError("Logger not configured. Call setup_logging() first.")
        return self._logger

    # def log_step(self, message: str, level: str = "info") -> None:
    #     """
    #     Log a message with an incremented step counter.

    #     Args:
    #         message: The message to log.
    #         level: The log level (default: info).
    #     """
    #     with self._lock:
    #         self._step_counter += 1
    #         log_message = f"STEP-{self._step_counter} :: {message}"

    #     log_methods = {
    #         "info": self._logger.info,
    #         "debug": self._logger.debug,
    #         "warning": self._logger.warning,
    #         "error": self._logger.error,
    #         "critical": self._logger.critical,
    #     }

    #     log_method = log_methods.get(level.lower(), self._logger.info)
    #     log_method(log_message)

    # def reset_log_step(self) -> None:
    #     """
    #     Reset the step counter.
    #     """
    #     with self._lock:
    #         self._step_counter = 0
