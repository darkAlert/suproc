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
                formatter = cls.AvaFormatter()
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


    class AvaFormatter(logging.Formatter):
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
        #Colors (requires ANSI escape codes):
        COLORS = {
            logging.DEBUG: '\x1b[38;21m',       # Grey
            logging.INFO: '\x1b[38;5;39m',      # Blue
            logging.WARNING: '\x1b[38;5;226m',  # Yellow
            logging.ERROR: '\x1b[38;5;196m',    # Red
            logging.CRITICAL: '\x1b[31;1m',     # Bold Red
            'RESET': '\x1b[0m'
        }

        def format(self, record):
            """
            Overrides the default format method to apply level-specific formatting.
            """
            # Select the format based on the log record's level
            fmt = self.FORMATS.get(record.levelno, self._fmt)

            # Create a new Formatter with the specific format string:
            formatter = logging.Formatter(fmt)

            # Apply:
            formatted_message = formatter.format(record)

            # Apply color:
            color_code = self.COLORS.get(record.levelno)
            if color_code:
                formatted_message = f"{color_code}{formatted_message}{self.COLORS['RESET']}"

            return formatted_message
