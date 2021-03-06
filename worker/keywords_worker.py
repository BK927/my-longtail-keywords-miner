import logging
import time
import random
import traceback
from typing import Tuple

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QWidget

from crawler.crawling_driver import CrawlingDriver


class KeywordsWorker(QThread):
    update = pyqtSignal(str, str, int, int, int, int, float)
    save_crawled_data = pyqtSignal(dict)
    crawling_finished = pyqtSignal()
    send_message = pyqtSignal(str)

    def __init__(self, driver: CrawlingDriver, category: Tuple[int, int, int, int], delay=(0, 0.3), recursive=True, parent=None):
        super().__init__()
        self.main = parent

        # Property
        self.recursive = recursive
        self._stop_flag = False
        self._category = category
        self._delay = delay

        # QtSignal
        parent.stop_signal.connect(self.stop)

        self.__driver = driver

    @property
    def delay(self) -> float:
        return random.uniform(self._delay[0], self._delay[1])

    @delay.setter
    def delay(self, delay: Tuple[int, int]):
        self._delay = delay

    def run(self):
        keywords_dic = self._create_empty_keyword_dict()
        try:
            if self.recursive:
                for t in self.__driver.crawl_keywords_recursive(self._category):
                    if self._stop_flag:
                        break
                    keywords_dic = self._add_to_dict(t[0], t[1], t[2], t[3], t[4], t[5], keywords_dic)
                    delay = self.delay
                    self.update.emit(t[0], t[1], t[2], t[3], t[4], t[5], delay + t[6])
                    time.sleep(delay)
            else:
                for t in self.__driver.crawl_keywords(self._category):
                    if self._stop_flag:
                        break
                    keywords_dic = self._add_to_dict(t[0], t[1], t[2], t[3], t[4], t[5], keywords_dic)
                    delay = self.delay
                    self.update.emit(t[0], t[1], t[2], t[3], t[4], t[5]. delay + t[6])
                    time.sleep(delay)
        except Exception as e:
            self.__driver.save_screenshot()
            err_message = str(e)
            logging.critical(err_message + " : " + traceback.format_exc())
            self.send_message.emit(err_message)
        finally:
            self.save_crawled_data.emit(keywords_dic)
            self.crawling_finished.emit()

    def stop(self):
        self._stop_flag = True

    def _create_empty_keyword_dict(self) -> dict:
        dic = {'분류': [], '키워드': [], '검색 수': [], '네이버 상품 수': []}
        if self.__driver.crawl_coupang:
            dic['쿠팡 상품 수'] = []
        if self.__driver.crawl_enuri:
            dic['에누리 상품 수'] = []
        return dic

    def _add_to_dict(self, category: str, keyword: str, qc_cnt: int, naver_products: int, coupang_products: int,
                      enuri_products: int, keywords_dic: dict):
        keywords_dic['분류'].append(category)
        keywords_dic['키워드'].append(keyword)
        keywords_dic['검색 수'].append(qc_cnt)
        keywords_dic['네이버 상품 수'].append(naver_products)
        if self.__driver.crawl_coupang:
            keywords_dic['쿠팡 상품 수'].append(coupang_products)
        if self.__driver.crawl_enuri:
            keywords_dic['에누리 상품 수'].append(enuri_products)
        return keywords_dic