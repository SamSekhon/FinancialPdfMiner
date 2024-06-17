import logging

logger = logging.getLogger(__name__)
fhandler = logging.FileHandler(filename="mylog.log", mode="w")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)
logger.setLevel(logging.DEBUG)


def get_logger():
    return logger
