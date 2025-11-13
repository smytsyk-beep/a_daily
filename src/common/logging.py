from loguru import logger


def setup_logging():
    logger.add("app.log", rotation="10 MB", retention="7 days")
