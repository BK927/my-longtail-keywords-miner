import logging
import time

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from typing import Tuple

from api.api_requester import NaverApi
from crawler.base_driver import BaseDriver
from crawler.naver_cache_driver import NaverCacheDriver
from crawler.xpath_container import NaverXpath, CoupangXpath, EnuriXpath


class CrawlingDriver(BaseDriver):
    # selenium crawler setting
    __cache_driver = NaverCacheDriver()

    __SLEEP_TIME = 2
    __SLEEP_WEIGHT = 0.5

    def __init__(self, crawl_coupang=False, crawl_enuri=False):
        super().__init__()
        self.__tabs = self._init_pages()
        self._crawl_coupang = crawl_coupang
        self._crawl_enuri = crawl_enuri
        self._last_setted_index = [0, 0, 0, 0]

    def _init_pages(self):
        self._driver.get(NaverXpath.url)
        # 기기별 전체 선택
        self._driver.find_element_by_xpath(NaverXpath.all_device_chkbox).click()
        # 성별 전체 선택
        self._driver.find_element_by_xpath(NaverXpath.both_gender_chkbox).click()
        # 연령별 전체 선택
        self._driver.find_element_by_xpath(NaverXpath.all_age_chkbox).click()

        self._driver.execute_script(f'window.open("{CoupangXpath.url}");')
        self._driver.execute_script(f'window.open("{EnuriXpath.url}");')

        # TODO : Figure out why it works like this
        tabs = {'naver': self._driver.window_handles[0], 'coupang': self._driver.window_handles[2],
                'enuri': self._driver.window_handles[1]}
        self._driver.switch_to.window(tabs['naver'])
        return tabs

    @property
    def crawl_coupang(self) -> bool:
        return self._crawl_coupang

    @crawl_coupang.setter
    def crawl_coupang(self, flag: bool):
        self._crawl_coupang = flag

    @property
    def crawl_enuri(self) -> bool:
        return self._crawl_enuri

    @crawl_enuri.setter
    def crawl_enuri(self, flag: bool):
        self._crawl_enuri = flag

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

        while len(index_stack) > 0:
            print(index_stack)
            logging.debug(index_stack)
            i = index_stack.pop()
            index_ls[depth - 1] = i

            if depth > 4 or not self.check_exists_by_xpath(NaverXpath.get_combobox(depth)):
                index_ls[depth - 1] = 0
                depth -= 1
                continue

            category_name = self.__cache_driver.get_category_name(tuple(index_ls))
            print(category_name)
            logging.debug(category_name)
            self._set_naver_category(tuple(index_ls))
            for t in self._crawl_current_category(category_name):
                yield t

            attr = self._driver.find_element_by_xpath(NaverXpath.get_combobox(depth)).get_attribute('class')
            if 'active' not in attr:
                self._driver.find_element_by_xpath(NaverXpath.get_combobox(depth)).click()

            no_available_in_current_depth = True
            if self.check_exists_by_xpath(NaverXpath.get_comboxbox_element(depth, i + 1)):
                logging.debug('Lower element exist')
                print('Lower element exist')
                index_stack.append(i + 1)
                no_available_in_current_depth = False

            if self.check_exists_by_xpath(NaverXpath.get_combobox(depth + 1)):
                logging.debug('Next depth exist')
                print('Next depth exist')
                depth += 1
                index_stack.append(1)
                no_available_in_current_depth = False

            if no_available_in_current_depth:
                index_ls[depth - 1] = 0
                depth -= 1

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
                if NaverXpath.page_btn_dsiabled_attr in self._driver.find_element_by_xpath(NaverXpath.next_page_btn).get_attribute('class'):
                    break
                if not self.check_exists_by_xpath(NaverXpath.get_keyword(i)):
                    break

                keyword = 'error'
                for j in range(10):
                    try:
                        raw = self._get_text(NaverXpath.get_keyword(i))
                        keyword = raw.split('\n')[1]
                        break
                    except StaleElementReferenceException:
                        if j > 5:
                            raise StaleElementReferenceException
                        else:
                            self.save_screenshot()
                            self._driver.find_element_by_xpath(NaverXpath.prev_page_btn).click()
                            time.sleep(5)
                            self.save_screenshot()
                            self._driver.find_element_by_xpath(NaverXpath.next_page_btn).click()
                            time.sleep(5)
                    except NoSuchElementException:
                        self.save_screenshot()
                        break

                monthly_qc_cnt = NaverApi.get_monthly_qc_cnt(keyword)
                naver_items = NaverApi.get_quantity_of_items(keyword)

                coupang_items = -2
                enuri_items = 2
                delay = 0

                if self._crawl_coupang:
                    delay += CrawlingDriver.__SLEEP_TIME
                    self._switch_to_coupang()
                    coupang_items = self._crawl_products_number(CoupangXpath.search_box, CoupangXpath.number_of_items, keyword)

                if self._crawl_enuri:
                    delay += CrawlingDriver.__SLEEP_TIME
                    self._switch_to_enuri()
                    enuri_items = self._crawl_products_number(EnuriXpath.search_box, EnuriXpath.number_of_itmes, keyword)


                self._switch_to_naver()
                yield category_name, keyword, monthly_qc_cnt, naver_items, coupang_items, enuri_items, delay

            # 다음 페이지 넘기기
            self._driver.find_element_by_xpath(NaverXpath.next_page_btn).click()

    def _switch_to_coupang(self) -> None:
        self._driver.switch_to.window(self.__tabs['coupang'])

    def _switch_to_naver(self) -> None:
        self._driver.switch_to.window(self.__tabs['naver'])

    def _switch_to_enuri(self) -> None:
        self._driver.switch_to_window(self.__tabs['enuri'])

    def _crawl_products_number(self, searchbox_xpath: str, number_xpath: str, keyword: str) -> int:
        number_of_items = -1
        is_crawling_successed = True

        try:
            form = self._driver.find_element_by_xpath(searchbox_xpath)
            form.clear()
            form.send_keys(keyword)
            form.submit()
        except NoSuchElementException:
            self.save_screenshot()
            CrawlingDriver.__SLEEP_TIME += CrawlingDriver.__SLEEP_WEIGHT
            time.sleep(CrawlingDriver.__SLEEP_TIME)
            self._driver.refresh()
            is_crawling_successed = False

        try:
            if is_crawling_successed:
                time.sleep(CrawlingDriver.__SLEEP_TIME)
                number_of_items = int(self._get_text(number_xpath).replace(',', ''))
        except NoSuchElementException:
            self.save_screenshot()
            number_of_items = 0
        except ValueError:
            self.save_screenshot()
            number_of_items = 0
        return number_of_items

    def _set_naver_category(self, index: Tuple[int, int, int, int]) -> None:
        for i in range(4):
            if index[i] == 0:
                break
            if index[i] == self._last_setted_index[i]:
                continue
            element = self._driver.find_element_by_xpath(NaverXpath.get_combobox(i + 1))
            attr = element.get_attribute('class')
            if NaverXpath.combobox_active_attr not in attr:
                element.click()
                time.sleep(0.3)
            self._driver.find_element_by_xpath(NaverXpath.get_comboxbox_element(i + 1, index[i])).click()
            self._last_setted_index[i] = index[i]
        self._driver.find_element_by_xpath(NaverXpath.lookup_btn).click()
        time.sleep(0.5)
