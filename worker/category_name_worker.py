from typing import Tuple

from PyQt5.QtCore import QThread, pyqtSignal

from crawler.naver_cache_driver import NaverCacheDriver


class CategoryNameWorker(QThread):
    crawling_finished = pyqtSignal()

    def __init__(self, delay: float, parent=None):
        super().__init__()
        self.main = parent

        self._driver = NaverCacheDriver()
        self._delay = delay

    def run(self):
        self._driver.update_file(self._delay)
        self.crawling_finished.emit()

    def set_delay(self, delay: float) -> None:
        self._delay = delay

    def is_cache_available(self) -> bool:
        return self._driver.try_to_load_cache()

    def get_next_category_list(self, index: Tuple[int, int, int, int]):
        return self._driver.get_next_category_list(index)
