import time

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from typing import Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from api.api_requester import NaverApi
from crawler.base_driver import BaseDriver
from crawler.naver_cache_driver import NaverCacheDriver
from crawler.xpath_container import NaverXpath, CoupangXpath


class CrawlingDriver(BaseDriver):
    # selenium crawler setting
    __naver_path = NaverXpath.url
    __coupang_path = CoupangXpath.url
    __cache_driver = NaverCacheDriver()

    __WAIT_TIME = 3

    def __init__(self):
        super().__init__()
        self.__tabs = self._init_pages()

    def _init_pages(self):
        self._driver.get(self.__naver_path)
        # 기기별 전체 선택
        self._driver.find_element_by_xpath(NaverXpath.all_device_chkbox).click()
        # 성별 전체 선택
        self._driver.find_element_by_xpath(NaverXpath.both_gender_chkbox).click()
        # 연령별 전체 선택
        self._driver.find_element_by_xpath(NaverXpath.all_age_chkbox).click()

        self._driver.execute_script(f'window.open("{self.__coupang_path}");')

        tabs = {'naver': self._driver.window_handles[0], 'coupang': self._driver.window_handles[1]}
        self._driver.switch_to.window(tabs['naver'])
        return tabs

    def get_number_of_products_from_coupang(self, keyword: str) -> int:
        self._clear_coupang_searchbox(CoupangXpath.search_box)
        self._search_on_coupang(CoupangXpath.search_box, keyword)
        if self.check_exists_by_xpath(CoupangXpath.number_of_items):
            text = self._driver.find_element_by_xpath(CoupangXpath.number_of_items).text.replace(',', '')
            return int(text)

        return -1

    def crawl_keywords_recursive(self, index: Tuple[int, int, int, int]):
        for data in self.crawl_keywords(index):
            yield data

        index_ls = list(index)
        position = self.__cache_driver.convert_to_current_position(index)
        depth = position[0] + 1
        index_stack = [1]

        while len(index_stack) > 0 and depth <= 4:
            i = index_stack.pop()
            index_ls[depth - 1] = i

            if self.check_exists_by_xpath(NaverXpath.get_combobox(depth)):
                index_ls[depth - 1] = 0
                depth -= 1
                continue

            category_name = self.__cache_driver.get_category_name(tuple(index_ls))
            self._set_naver_category(tuple(index_ls))
            for t in self._crawl_current_category(category_name):
                yield t

            if self.check_exists_by_xpath(NaverXpath.get_comboxbox_element(depth, i)):
                index_stack.append(i + 1)
                index_ls[depth - 1] = i + 1

            if self.check_exists_by_xpath(NaverXpath.get_combobox(depth + 1)):
                depth += 1
                index_stack.append(1)
                index_ls[depth - 1] = 1

    def crawl_keywords(self, index: Tuple[int, int, int, int]):
        self._switch_to_naver()
        self._set_naver_category(index)
        category_name = self.__cache_driver.get_category_name(index)
        for t in self._crawl_current_category(category_name):
            yield t

    def _crawl_current_category(self, category_name: str):
        # 키워드 크롤링 구문
        for p in range(0, 25):
            # 인기검색어 가져오기
            for i in range(1, 21):
                if not self.check_exists_by_xpath(NaverXpath.get_keyword(i)):
                    break
                raw = self._get_text(NaverXpath.get_keyword(i))

                keyword = raw.split('\n')[1]
                monthly_qc_cnt = NaverApi.get_monthly_qc_cnt(keyword)
                naver_items = NaverApi.get_quantity_of_items(keyword)

                self._switch_to_coupang()

                coupang_items = -1
                coupang_flag = True

                try:
                    self._clear_coupang_searchbox()
                    self._search_on_coupang(keyword)
                except NoSuchElementException:
                    self._driver.get(CoupangXpath.url)
                    coupang_flag = False

                try:
                    if coupang_flag:
                        coupang_items = int(self._get_text(CoupangXpath.number_of_items).replace(',', ''))
                except NoSuchElementException:
                    coupang_items = 0

                self._switch_to_naver()

                yield category_name, keyword, monthly_qc_cnt, naver_items, coupang_items

            # 다음 페이지 넘기기
            self._driver.find_element_by_xpath(NaverXpath.next_page_btn).click()

    def _switch_to_coupang(self) -> None:
        self._driver.switch_to.window(self.__tabs['coupang'])

    def _switch_to_naver(self) -> None:
        self._driver.switch_to.window(self.__tabs['naver'])

    def _search_on_coupang(self, keyword: str) -> None:
        form = self._driver.find_element_by_xpath(CoupangXpath.search_box)
        form.send_keys(keyword)
        form.submit()

    def _clear_coupang_searchbox(self) -> None:
        form = self._driver.find_element_by_xpath(CoupangXpath.search_box)
        form.clear()

    def _set_naver_category(self, index: Tuple[int, int, int, int]) -> None:
        for i in range(4):
            if index[i] == 0:
                break
            self._driver.find_element_by_xpath(NaverXpath.get_combobox(i + 1)).click()
            time.sleep(0.3)
            self._driver.find_element_by_xpath(NaverXpath.get_comboxbox_element(i + 1, index[i])).click()
        self._driver.find_element_by_xpath(NaverXpath.lookup_btn).click()
        time.sleep(0.5)
