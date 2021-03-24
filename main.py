import logging
import os
import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pandas as pd
from typing import List, Tuple

from crawler.crawling_driver import CrawlingDriver
from crawler.keywords_miner import KeywordsMiner
from crawler.naver_cache_driver import NaverCacheDriver

main_window = uic.loadUiType('./ui/main_window.ui')[0]
debug_window = uic.loadUiType('./ui/debug_window.ui')


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
        #KeywordsMiner.update.connect(self._update)
        #KeywordsMiner.save_crawled_data.connect(self._save_datatable)
        #KeywordsMiner.crawling_finished.connect(self.stop_crawling)

        self.crawlBtn.clicked.connect(self.crawlBtn_clicked)
        self.stopBtn.clicked.connect(self.stopBtn_clicked)
        self.category1.activated.connect(lambda index: self.category_activated(index, self.category2))
        self.category2.activated.connect(lambda index: self.category_activated(index, self.category3))
        self.category3.activated.connect(lambda index: self.category_activated(index, self.category4))
        # self.category4.activated.connect(lambda index: self.category_activated(index, self.category4))

        # initiate comboboxes
        for combobox in self._comboboxes:
            self._reset_combobox(combobox)
        self.category_activated(-1, self.category1)

    @property
    def is_crawling(self):
        return self.__is_crawling

    @is_crawling.setter
    def is_crawling(self, value):
        self.__is_crawling = value

        if value:
            self.stopBtn.setEnabled(True)
            self.category1.setEnabled(False)
            self.category2.setEnabled(False)
            self.category3.setEnabled(False)
            self.category4.setEnabled(False)
            self.crawlBtn.setEnabled(False)
            self.progressBar.setMaximum(0)
        else:
            self.stopBtn.setEnabled(False)
            self.category1.setEnabled(True)
            self.category2.setEnabled(True)
            self.category3.setEnabled(True)
            self.category4.setEnabled(True)
            self.crawlBtn.setEnabled(True)
            self.progressBar.setMaximum(1)

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

        ls = NaverCacheDriver.get_next_category_list(
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

        keywords_miner = self._create_keywords_miner(self._convert_comboboxes_to_indexes())
        keywords_miner.start()
        self.is_crawling = True

    def stopBtn_clicked(self):
        self._miner.stop()
        self.stopBtn.setEnabled(False)

    def stop_crawling(self):
        self.is_crawling = False

    def _load_category_items(self, comboBox: QComboBox):
        index_ls = []
        for c in self._comboboxes:
            index_ls.append(c.currentIndex())
        depth = NaverCacheDriver.convert_to_current_depth(tuple(index_ls))

    def _reset_combobox(self, comboBox: QComboBox):
        comboBox.clear()
        i = comboBox.property('depth')
        comboBox.addItem(f'--{str(i)}분류--')

    def _convert_comboboxes_to_indexes(self) -> Tuple[int, int, int, int]:
        indexes = []
        for c in self._comboboxes:
            indexes.append(c.currentIndex())
        return tuple(indexes)

    def _update(self, category: str, keyword: str, qc_cnt: int, num_of_naver: int, num_of_coupang: int, delay: float):
        self._add_row_to_table(category, keyword, qc_cnt, num_of_naver, num_of_coupang)
        t = round(delay, 2)
        self.delayTimeLabel.setText(str(t))

    def _add_row_to_table(self, category: str, keyword: str, qc_cnt: int, naver_products: int, coupang_products: int):
        i = self.dataTable.rowCount()
        self.dataTable.insertRow(i)

        self.dataTable.setItem(i, 0, QTableWidgetItem(category))
        self.dataTable.setItem(i, 1, QTableWidgetItem(keyword))
        self.dataTable.setItem(i, 2, QTableWidgetItem(str(qc_cnt)))
        self.dataTable.setItem(i, 3, QTableWidgetItem(str(naver_products)))
        self.dataTable.setItem(i, 4, QTableWidgetItem(str(coupang_products)))

    def _save_datatable(self, keywords_dic):
        min_length = len(keywords_dic['분류'])

        for ls in keywords_dic.values():
            if len(ls) < min_length:
                min_length = len(ls)

        for ls in keywords_dic.values():
            del ls[min_length:]

        filedir = QFileDialog.getSaveFileName(self, 'Save file', './', 'Exel File(*.xlsx)')
        keywords_df = pd.DataFrame(keywords_dic)
        keywords_df.to_excel(filedir[0] + '.xlsx', index=False)

        self._miner = None

    def _create_keywords_miner(self, index: Tuple[int, int, int, int]) -> KeywordsMiner:
        if self._miner is None:
            miner = KeywordsMiner(self._crawling_driver, self._convert_comboboxes_to_indexes(),
                                  recursive=self.RecursivieChkBox.isChecked(), parent=self)
            miner.update.connect(self._update)
            miner.save_crawled_data.connect(self._save_datatable)
            miner.crawling_finished.connect(self.stop_crawling)
        return miner


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    if not os.path.exists('./log'):
        os.mkdir('./log')
    logging.basicConfig(filename='./log/debug.log',
                        filemode='a',
                        format='%(asctime)s - %(thread)d - %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

    app.exec_()
