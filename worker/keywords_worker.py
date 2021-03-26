import logging
import time
import random
import traceback
from typing import Tuple

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QWidget

from crawler.crawling_driver import CrawlingDriver


class KeywordsWorker(QThread):
    update = pyqtSignal(str, str, int, int, int, float)
    save_crawled_data = pyqtSignal(dict)
    crawling_finished = pyqtSignal()

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
                    keywords_dic = self._add_to_dict(t[0], t[1], t[2], t[3], t[4], keywords_dic)
                    delay = self.delay
                    self.update.emit(t[0], t[1], t[2], t[3], t[4], delay + t[5])
                    time.sleep(delay)
            else:
                for t in self.__driver.crawl_keywords(self._category):
                    if self._stop_flag:
                        break
                    keywords_dic = self._add_to_dict(t[0], t[1], t[2], t[3], t[4], keywords_dic)
                    delay = self.delay
                    self.update.emit(t[0], t[1], t[2], t[3], t[4], delay + t[5])
                    time.sleep(delay)
        except Exception as e:
            self.__driver.save_screenshot()
            err_message = str(e)
            logging.critical(err_message + " : " + traceback.format_exc())
            QMessageBox.critical(self.main, '오류', '치명적 오류 발생: ' + err_message)
        finally:
            self.save_crawled_data.emit(keywords_dic)
            self.crawling_finished.emit()

    def stop(self):
        self._stop_flag = True

    def _send_data(self, category: str, keyword: str, qc_cnt: int, naver_products: int, coupang_products: int) -> None:
        self.update.emit(category, keyword, qc_cnt, naver_products, coupang_products)

    def _create_empty_keyword_dict(self) -> dict:
        return {'분류': [], '키워드': [], '검색 수': [], '네이버 상품 수': [], '쿠팡 상품 수': []}

    def _add_to_dict(self, category: str, keyword: str, qc_cnt: int, naver_products: int, coupang_products: int,
                      keywords_dic: dict):
        keywords_dic['분류'].append(category)
        keywords_dic['키워드'].append(keyword)
        keywords_dic['검색 수'].append(qc_cnt)
        keywords_dic['네이버 상품 수'].append(naver_products)
        keywords_dic['쿠팡 상품 수'].append(coupang_products)
        return keywords_dic