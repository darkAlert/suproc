"""
AVA Single Unique Process
© AVA, 2025
"""
import logging
import sys


class AvaLogger:
    _loggers = {}

    @classmethod
    def get_logger(cls, name, path=None, formatter=None):
        if name not in cls._loggers:
            if formatter is None:
                formatter = None #cls.Formatter
            AvaLogger._loggers[name] = (cls._create_logger(name, path=path, formatter=formatter), path)

        logger, _path = AvaLogger._loggers[name]
        if _path != path:
            logger.warning(f"Logger '{name}' is already created with a different log path: '{_path}'")

        return logger

    @staticmethod
    def _create_logger(name, path=None, formatter=None):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Log file:
        if path is not None:
            handler = logging.FileHandler(filename=path)
        else:
            handler = logging.StreamHandler(sys.stdout)

        # Set formatter:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger


    class Formatter(logging.Formatter):
        """
        A custom formatter that uses different format strings for different log levels.
        """
        FORMATS = {
            logging.DEBUG: "%(message)s",
            logging.INFO: "[%(name)s] %(message)s",
            logging.WARNING: "[%(name)s:%(levelname)s] %(message)s",
            logging.ERROR: "[%(name)s:%(levelname)s] %(message)s",
            logging.CRITICAL: "%(asctime)s - CRITICAL - !!! %(message)s !!!",
        }

        def format(self, record):
            """
            Overrides the default format method to apply level-specific formatting.
            """
            # Store the original format
            original_format = self._fmt

            # Select the format based on the log record's level
            self._fmt = self.FORMATS.get(record.levelno, self._fmt)

            # Format the record
            formatted_message = super().format(record)

            # Restore the original format for subsequent records (important for shared formatters)
            self._fmt = original_format

            return formatted_message