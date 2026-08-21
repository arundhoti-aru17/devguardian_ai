import logging
import sys

# Create logger
logger = logging.getLogger("devguardian")

# Avoid adding handlers if already configured (e.g., by main.py)
if not logger.handlers:
    # Handler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    console_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)


def get_logger(name: str = "devguardian") -> logging.Logger:
    """
    Get a configured logger instance.

    Usage:

        from app.core.logging import get_logger

        log = get_logger(__name__)
        log.info("Event occurred")
        log.error("Something failed", exc_info=True)
    """

    return logging.getLogger(name)