import logging


def get_logger(
    name: str,
    log_path: str = "",
    log_level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
):
    """Returns a logger. if `log_path` is given it will log to the specified file otherwise to console."""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    formatter = logging.Formatter(format)
    if logger.hasHandlers():
        logger.handlers.clear()
    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
