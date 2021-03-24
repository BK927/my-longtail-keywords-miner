import time
import random
from typing import Tuple

from PyQt5.QtCore import QThread, pyqtSignal
from crawler.crawling_driver import CrawlingDriver


class KeywordsMiner(QThread):
    update = pyqtSignal(str, str, int, int, int, float)
    save_crawled_data = pyqtSignal(dict)
    crawling_finished = pyqtSignal()

    def __init__(self, driver: CrawlingDriver, category: Tuple[int, int, int, int], recursive=True, parent=None):
        super().__init__()

        # Property
        self.main = parent
        self.recursive = recursive
        self._stop_flag = False
        self._category = category

        # QtSignal
        parent.stop_signal.connect(self.stop)

        self.__driver = driver

    def run(self):
        keywords_dic = self._create_empty_keyword_dict()
        if self.recursive:
            for t in self.__driver.crawl_keywords_recursive(self._category):
                if self._stop_flag:
                    break
                keywords_dic = self._add_to_dict(t[0], t[1], t[2], t[3], t[4], keywords_dic)
                delay = random.uniform(1, 2)
                self.update.emit(t[0], t[1], t[2], t[3], t[4], delay)
                time.sleep(delay)
        else:
            for t in self.__driver.crawl_keywords(self._category):
                if self._stop_flag:
                    break
                keywords_dic = self._add_to_dict(t[0], t[1], t[2], t[3], t[4], keywords_dic)
                delay = random.uniform(1, 2)
                self.update.emit(t[0], t[1], t[2], t[3], t[4], delay)
                time.sleep(delay)
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