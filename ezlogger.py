import logging
from typing import Union


class EzLogger:
    err_logger = logging.getLogger("error")

    @staticmethod
    def logfile(level: Union[int, str], message: str) -> None:
        EzLogger.err_logger.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        stream_hander = logging.StreamHandler()
        stream_hander.setFormatter(formatter)
        EzLogger.err_logger.addHandler(stream_hander)

        file_handler = logging.FileHandler('./log/err.log')
        EzLogger.err_logger.addHandler(file_handler)

        if level == logging.WARNING:
            EzLogger.err_logger.warning(message)
        elif level == logging.INFO:
            EzLogger.err_logger.info(message)
        elif level == logging.ERROR:
            EzLogger.err_logger.error(message)
