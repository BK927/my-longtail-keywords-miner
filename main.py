import sys

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pandas as pd

from category_enum import Category
from keywords_miner import KeywordsMiner

main_window = uic.loadUiType('./ui/main_window.ui')[0]
debug_window = uic.loadUiType('./ui/debug_window.ui')


class MyWindow(QMainWindow, main_window):
    stop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Properties
        self._keywords_miner = KeywordsMiner(parent=self)
        self.__isCrawling = False

        # initiate slots
        self._keywords_miner.update.connect(self._update)
        self._keywords_miner.save_crawled_data.connect(self.__save_datatable)
        self._keywords_miner.crawling_finished.connect(self.stop_crawling)

        self.crawlBtn.clicked.connect(self._crawlBtn_clicked)
        self.stopBtn.clicked.connect(self._stopBtn_clicked)
        self.category1.activated.connect(lambda index: self._category_activated(index, self.category1))
        self.category2.activated.connect(lambda index: self._category_activated(index, self.category2))
        self.category3.activated.connect(lambda index: self._category_activated(index, self.category3))
        self.category4.activated.connect(lambda index: self._category_activated(index, self.category4))

        # initiate comboboxes
        self.category1.addItem('--1분류--')
        self.category2.addItem('--2분류--')
        self.category3.addItem('--3분류--')
        self.category4.addItem('--4분류--')

        self._load_category_items(Category.category1, self.category1)

    def __del__(self):
        self._keywords_miner.quit()

    @property
    def is_crawling(self):
        return self.__isCrawling

    @is_crawling.setter
    def is_crawling(self, value):
        self.__isCrawling = value

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

    def stop_crawling(self):
        self.is_crawling = False

    def _load_category_items(self, category: Category, comboBox: QComboBox):
        self._reset_combobox(comboBox)

        ls = self._keywords_miner.get_naver_category_list(category)
        for item in ls:
            comboBox.addItem(item)

        comboBox.setCurrentIndex(0)

    def _category_activated(self, index: int, comboBox: QComboBox):
        if index <= 0:
            return

        category = Category(comboBox.property('category'))
        self._keywords_miner.click_item(category, index)

        next_combobox = self._get_next_combobox(comboBox)

        if category.value < 4:
            self._load_category_items(Category(category.value + 1), next_combobox)

        for c in self._get_combobox_list():
            if c.property('category') > next_combobox.property('category'):
                self._reset_combobox(c)

    def _get_combobox_list(self):
        return [self.category1, self.category2, self.category3, self.category4]

    def _get_next_combobox(self, comboBox: QComboBox) -> QComboBox:
        ls = self._get_combobox_list()
        index = ls.index(comboBox)
        return ls[index + 1]

    def _reset_combobox(self, comboBox: QComboBox):
        comboBox.clear()
        i = comboBox.property('category')
        comboBox.addItem(f'--{str(i)}분류--')

    def _update(self, category: str, keyword: str, qc_cnt: int, num_of_naver: int, num_of_coupang: int, delay: float):
        self._add_row_to_table(category, keyword, qc_cnt, num_of_naver, num_of_coupang)
        t = round(delay, 2)
        self.delayTimeLabel.setText(str(t))

    def _add_row_to_table(self, category: str, keyword: str, qc_cnt: int, num_of_naver: int, num_of_coupang: int):
        i = self.dataTable.rowCount()
        self.dataTable.insertRow(i)

        self.dataTable.setItem(i, 0, QTableWidgetItem(category))
        self.dataTable.setItem(i, 1, QTableWidgetItem(keyword))
        self.dataTable.setItem(i, 2, QTableWidgetItem(str(qc_cnt)))
        self.dataTable.setItem(i, 3, QTableWidgetItem(str(num_of_naver)))
        self.dataTable.setItem(i, 4, QTableWidgetItem(str(num_of_coupang)))

    def _crawlBtn_clicked(self):
        if self.category1.currentIndex() == 0:
            QMessageBox.about(self, '에러', '최소 한 분류 이상을 선택해야 크롤링이 가능합니다')
            return

        self.is_crawling = True

        self._keywords_miner.isRun = True
        self._keywords_miner.start()

    def _stopBtn_clicked(self):
        self.stop_signal.emit()
        self.stopBtn.setEnabled(False)

    def __save_datatable(self, keywords_dic):
        min_length = len(keywords_dic['분류'])

        for ls in keywords_dic.values():
            if len(ls) < min_length:
                min_length = len(ls)

        for ls in keywords_dic.values():
            del ls[min_length:]

        filedir = QFileDialog.getSaveFileName(self, 'Save file', './', 'Exel File(*.xlsx)')
        keywords_df = pd.DataFrame(keywords_dic)
        keywords_df.to_excel(filedir[0] + '.xlsx', index=False)

        self._keywords_miner.isRun = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
