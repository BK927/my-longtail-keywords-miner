import logging
from typing import Union


class EzLogger:
    logging.basicConfig(filename='./log/debug.log',
                        filemode='a',
                        format='%(asctime)s - %(thread)d - %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

    @staticmethod
    def logfile(level: Union[int, str], message: str) -> None:
        logging.info(message)

        print(message)
