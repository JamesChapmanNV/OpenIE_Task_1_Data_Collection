import logging
import sys

def setup_logger(name="oie", level="INFO"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)
    h = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("[%(levelname)s] %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
    return logger

