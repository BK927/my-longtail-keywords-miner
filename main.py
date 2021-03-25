import logging
import os
import platform
import sys
from enum import Enum

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pandas as pd
from typing import List, Tuple

if not os.path.exists('./log'):
    os.mkdir('./log')

from crawler.crawling_driver import CrawlingDriver
from worker.category_name_worker import CategoryNameWorker
from worker.keywords_worker import KeywordsWorker
from crawler.naver_cache_driver import NaverCacheDriver

main_window = uic.loadUiType('./ui/main_window.ui')[0]

logging.basicConfig(filename='./log/debug.log',
                    filemode='a',
                    format='%(asctime)s - %(thread)d - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

class State(Enum):
    Idle = 0
    Crawling = 1
    Caching = 2

class MainWindow(QMainWindow, main_window):
    stop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Properties
        self._crawling_driver = CrawlingDriver()
        self._category_cache_driver = NaverCacheDriver()
        self._comboboxes: List[QComboBox, ...] = [self.category1, self.category2, self.category3, self.category4]
        self.__is_crawling = False
        self._miner = None

        # initiate slots
        self.crawlBtn.clicked.connect(self.crawlBtn_clicked)
        self.stopBtn.clicked.connect(self.stopBtn_clicked)
        self.category1.activated.connect(lambda index: self.category_activated(index, self.category2))
        self.category2.activated.connect(lambda index: self.category_activated(index, self.category3))
        self.category3.activated.connect(lambda index: self.category_activated(index, self.category4))

        # category name loading
        self._cache_worker = CategoryNameWorker(5, parent=self)
        if self._cache_worker.is_cache_available():
            self._initiate_comboboxes()
        else:
            self._cache_worker.set_delay(0.4)
            self._start_category_caching()
            QMessageBox.about(self, '알림', '카테고리 데이터를 다운로드합니다. 해당 작업은 프로그램 첫실행에만 실행됩니다.')
        self._cache_worker.crawling_finished.connect(self._finished_category_caching)
        self._cache_worker.start()

    @property
    def is_crawling(self):
        return self.__is_crawling

    @is_crawling.setter
    def is_crawling(self, value):
        self.__is_crawling = value
        if value:
            self._set_state(State.Crawling)
        else:
            self._set_state(State.Idle)

    def category_activated(self, index: int, next_comboBox: QComboBox):
        if index == 0:
            return

        for c in self._comboboxes:
            if c.property('depth') > next_comboBox.property('depth') - 1:
                self._reset_combobox(c)
            if c.property('depth') > next_comboBox.property('depth'):
                c.setEnabled(False)
            else:
                c.setEnabled(True)

        ls = self._cache_worker.get_next_category_list(
            (self.category1.currentIndex(), self.category2.currentIndex(),
             self.category3.currentIndex(), self.category4.currentIndex()))

        for item in ls:
            next_comboBox.addItem(item)
        if not ls:
            next_comboBox.setEnabled(False)

    def crawlBtn_clicked(self):
        if self.category1.currentIndex() == 0:
            QMessageBox.about(self, '에러', '최소 한 분류 이상을 선택해야 크롤링이 가능합니다')
            return
        self.dataTable.setRowCount(0)
        self.is_crawling = True
        keywords_miner = self._create_keywords_miner(self._convert_comboboxes_to_indexes())
        keywords_miner.start()

    def stopBtn_clicked(self):
        self._miner.stop()
        self.stopBtn.setEnabled(False)

    def stop_crawling(self):
        self.is_crawling = False

    def _set_state(self, state: State):
        comboboxes = self.findChildren(QComboBox)
        if state == State.Idle:
            for c in comboboxes:
                c.setEnabled(True)
            self.crawlBtn.setEnabled(True)
            self.stopBtn.setEnabled(False)
            self.progressBar.setMaximum(1)
        elif state == State.Crawling:
            for c in comboboxes:
                c.setEnabled(False)
            self.crawlBtn.setEnabled(False)
            self.stopBtn.setEnabled(True)
            self.progressBar.setMaximum(0)
        elif state == State.Caching:
            for c in comboboxes:
                c.setEnabled(False)
            self.crawlBtn.setEnabled(False)
            self.stopBtn.setEnabled(False)
            self.progressBar.setMaximum(0)

    def _initiate_comboboxes(self):
        for combobox in self._comboboxes:
            self._reset_combobox(combobox)
        self.category_activated(-1, self.category1)

    def _reset_combobox(self, comboBox: QComboBox):
        comboBox.clear()
        i = comboBox.property('depth')
        comboBox.addItem(f'--{str(i)}분류--')

    def _convert_comboboxes_to_indexes(self) -> Tuple[int, int, int, int]:
        indexes = []
        for c in self._comboboxes:
            indexes.append(c.currentIndex())
        return tuple(indexes)

    def _start_category_caching(self):
        self._set_state(State.Caching)

    def _finished_category_caching(self):
        if not self.is_crawling:
            self._set_state(State.Idle)
            QMessageBox.about(self, '', '카테고리 다운로드를 완료 했습니다.')
            self._initiate_comboboxes()

    def _update(self, category: str, keyword: str, qc_cnt: int, num_of_naver: int, num_of_coupang: int, delay: float) -> None:
        self._add_row_to_table(category, keyword, qc_cnt, num_of_naver, num_of_coupang)
        t = round(delay, 2)
        self.delayTimeLabel.setText(str(t))

    def _add_row_to_table(self, category: str, keyword: str, qc_cnt: int, naver_products: int, coupang_products: int) -> None:
        i = self.dataTable.rowCount()
        self.dataTable.insertRow(i)

        self.dataTable.setItem(i, 0, QTableWidgetItem(category))
        self.dataTable.setItem(i, 1, QTableWidgetItem(keyword))
        self.dataTable.setItem(i, 2, QTableWidgetItem(str(qc_cnt)))
        self.dataTable.setItem(i, 3, QTableWidgetItem(str(naver_products)))
        self.dataTable.setItem(i, 4, QTableWidgetItem(str(coupang_products)))

    def _save_datatable(self, keywords_dic) -> None:
        self._miner = None
        min_length = len(keywords_dic['분류'])

        for ls in keywords_dic.values():
            if len(ls) < min_length:
                min_length = len(ls)

        for ls in keywords_dic.values():
            del ls[min_length:]

        filedir = QFileDialog.getSaveFileName(self, 'Save file', './', 'Exel File(*.xlsx)')

        if filedir[0] == '':
            return

        keywords_df = pd.DataFrame(keywords_dic)
        if platform.system() == 'Linux':
            keywords_df.to_excel(filedir[0] + '.xlsx', index=False)
        else:
            keywords_df.to_excel(filedir[0], index=False)

    def _create_keywords_miner(self, index: Tuple[int, int, int, int]) -> KeywordsWorker:
        if self._miner is None:
            self._miner = KeywordsWorker(self._crawling_driver, index,
                                         recursive=self.RecursivieChkBox.isChecked(), parent=self)
            self._miner.update.connect(self._update)
            self._miner.save_crawled_data.connect(self._save_datatable)
            self._miner.crawling_finished.connect(self.stop_crawling)
        return self._miner


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()
