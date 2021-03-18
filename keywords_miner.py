import time
import random

from PyQt5.QtCore import QThread, pyqtSignal
from selenium.common.exceptions import NoSuchElementException

from api.api_requester import NaverApi
from category_enum import Category
from ezdriver import EzDriver
from xpath_container import NaverXpath, CoupangXpath


class KeywordsMiner(QThread):
    send_category_and_index = pyqtSignal(dict)
    update = pyqtSignal(str, str, int, int, int, float)
    save_crawled_data = pyqtSignal(dict)
    crawling_finished = pyqtSignal()

    __categories = {Category.category1: 1, Category.category2: 2, Category.category3: 3, Category.category4: 4}

    def __init__(self, parent=None):
        super().__init__()
        self.main = parent
        self.isRun = False
        parent.stop_signal.connect(self.stop)

        self.__driver = EzDriver()
        self.__last_selected_category = Category.category1
        self.__last_selected_index = 0

    def __del__(self):
        self.working = False
        self.quit()
        self.__driver.quit()
        self.wait(500)

    def run(self):
        keywords_dic = self.mine_keywords(self.__last_selected_category, self.__last_selected_index)
        self.save_crawled_data.emit(keywords_dic)
        self.crawling_finished.emit()

    def stop(self):
        self.isRun = False

    def get_naver_category_list(self, category: Category) -> []:
        depth = category.value
        if not self.__driver.check_exists_by_xpath(NaverXpath.get_combobox(depth)):
            return []

        # Open the combobox
        self.__driver.click(NaverXpath.get_combobox(depth))

        time.sleep(0.2)

        # Get item list
        items = self.__driver.find_elements(NaverXpath.get_comboxbox_list(depth))

        ls = []

        # Append items to python list
        for item in items:
            ls.append(item.text)

        # Close the combobox
        self.__driver.click(NaverXpath.get_combobox(depth))

        return ls

    def click_item(self, category: Category, index: int):
        depth = category.value

        # Open the combobox
        self.__driver.click(NaverXpath.get_combobox(depth))

        # Click the element of the combobox
        self.__driver.click(NaverXpath.get_comboxbox_element(depth, index))

        self.__check_last_selected(category, index)

    def __create_empty_keywords_dic(self):
        keywords_dic = {'분류': [], '키워드': [], '검색 수': [], '네이버 상품 수': [], '쿠팡 상품 수': []}
        return keywords_dic

    # TODO: 끝에 메인 UI와 싱크 추가
    def mine_keywords(self, category: Category, index: int) -> {}:
        keywords_dic = self.__create_empty_keywords_dic()
        self.click_item(category, index)

        category_text = self.__driver.get_text(NaverXpath.get_combobox_title(category.value))

        self._crawl_current_page(category_text, keywords_dic)

        next_category = Category(category.value + 1)
        self._crawl_keywords_recursive(next_category, keywords_dic)
        return keywords_dic

    def _crawl_current_page(self, category_text: str, keywords_dic) -> None:
        if not self.isRun:
            return

        self.__driver.click(NaverXpath.lookup_btn)
        time.sleep(random.uniform(0.5, 1))

        # 키워드 크롤링 구문
        for p in range(0, 25):
            # 인기검색어 가져오기
            for i in range(1, 21):
                if not self.isRun:
                    return

                if not self.__driver.check_exists_by_xpath(NaverXpath.get_keyword(i)):
                    break
                raw = self.__driver.get_text(NaverXpath.get_keyword(i))
                keyword = raw.split('\n')[1]

                keywords_dic['분류'].append(category_text)
                keywords_dic['키워드'].append(keyword)

                monthly_qc_cnt = NaverApi.get_monthly_qc_cnt(keyword)
                keywords_dic['검색 수'].append(monthly_qc_cnt)

                naver_items = NaverApi.get_quantity_of_items(keyword)
                keywords_dic['네이버 상품 수'].append(naver_items)

                self.__driver.switch_to_coupang()
                self.__driver.clear_searchbox(CoupangXpath.search_box)
                self.__driver.search(CoupangXpath.search_box, keyword)
                try:
                    coupamg_items = int(self.__driver.get_text(CoupangXpath.number_of_items).replace(',', ''))
                    keywords_dic['쿠팡 상품 수'].append(coupamg_items)
                except NoSuchElementException:
                    keywords_dic['쿠팡 상품 수'].append(0)

                # update subscribers
                delay = random.uniform(1, 2)
                self.__driver.switch_to_naver()

                self.update.emit(category_text, keyword, monthly_qc_cnt, naver_items, coupamg_items, delay)

                time.sleep(delay)

            # 다음 페이지 넘기기
            self.__driver.click(NaverXpath.next_page_btn)

    # TODO: 분류이름 버그 수정
    def _crawl_keywords_recursive(self, category: Category, keywords_dic) -> None:
        if not self.__driver.check_exists_by_xpath(NaverXpath.get_combobox(category.value)):
            return

        comboxbox_ls = self.__driver.find_elements(NaverXpath.get_comboxbox_list(category.value))

        for i in range(1, len(comboxbox_ls)):
            if not self.isRun:
                return

            category_text = self.__driver.get_text(NaverXpath.get_combobox_title(category.value))

            self.click_item(category, i)
            self._crawl_current_page(category_text, keywords_dic)

            # base condition
            if category.value < 4:
                next_category = Category(category.value + 1)
                self._crawl_keywords_recursive(next_category, keywords_dic)

    def __check_last_selected(self, category: Category, index: int):
        self.__last_selected_category = category
        self.__last_selected_index = index