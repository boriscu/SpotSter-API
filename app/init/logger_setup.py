import os
import logging
from typing import Optional


class LoggerSetup:
    """
    Configures and provides named loggers with file-based handlers.
    Each logger writes to a dedicated log file under the logs directory.
    """

    def __init__(self, log_name: str, log_dir: str, file_name_format: str):
        self.log_name = log_name
        self.log_dir = os.path.join("logs", log_dir)
        self.file_name_format = file_name_format
        self.ensure_log_dir_exists()

    def ensure_log_dir_exists(self) -> None:
        """Creates the log directory if it does not already exist."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def setup_logger(self) -> logging.Logger:
        """
        Creates and returns a configured logger with a file handler.

        Returns:
            logging.Logger: A logger instance writing to the configured file.
        """
        logger = logging.getLogger(self.log_name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            log_path = os.path.join(self.log_dir, self.file_name_format)
            file_handler = logging.FileHandler(log_path)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @classmethod
    def get_logger(cls, entity: str, entity_id: Optional[int] = None) -> logging.Logger:
        """
        Retrieves a logger configured for a specific entity.

        Args:
            entity: The name of the entity for which the logger is created.
                    Supported entities are 'cli', 'migrations', 'general', and 'errors'.
            entity_id: Optional ID to distinguish logs by entity instance.

        Returns:
            logging.Logger: A configured logger with an appropriate handler and format set.

        Raises:
            KeyError: If the specified entity is not supported.
        """
        loggers = {
            "cli": cls("cli_output", "cli_output", "cli_output.log"),
            "migrations": cls("migrations", "migrations", "migrations.log"),
            "general": cls("general", "general", "general.log"),
            "errors": cls("errors", "errors", "errors.log"),
        }
        return loggers[entity].setup_logger()
