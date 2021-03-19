import platform

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from typing import List, Tuple

from category_enum import Category
from ini_reader import IniReader
from xpath_container import NaverXpath, CoupangXpath

try:
    from pyvirtualdisplay import Display
except:
    pass


class EzDriver:
    # selenium driver setting
    __naver_path = NaverXpath.url
    __coupang_path = CoupangXpath.url
    __driver_path = IniReader.DRIVER_PATH
    __service_log_path = "log/chromedriver.log"
    __service_args = ['--verbose']

    __WAIT_TIME = 3

    def __init__(self):
        self.__driver = self._init_driver()
        self.__tabs = self._init_pages()

    def _init_driver(self) -> WebDriver:
        if platform.system() == 'Linux':
            display = Display(visible=True, size=(1920, 1080))
            display.start()

        options = webdriver.ChromeOptions()
        # headless 옵션 설정
        if IniReader.HEADLESS == 'TRUE':
            options.add_argument('headless')
        if IniReader.NO_SANDBOX == 'TRUE':
            options.add_argument("no-sandbox")

        # 브라우저 윈도우 사이즈
        options.add_argument('window-size=1920x1080')

        # 사람처럼 보이게 하는 옵션들
        options.add_argument("disable-gpu")  # 가속 사용 x
        options.add_argument("lang=ko_KR")  # 가짜 플러그인 탑재
        options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/61.0.3163.100 Safari/537.36')  # user-agent 이름 설정

        driver = webdriver.Chrome(EzDriver.__driver_path,
                                  service_args=EzDriver.__service_args,
                                  service_log_path=EzDriver.__service_log_path,
                                  chrome_options=options)

        driver.implicitly_wait(self.__WAIT_TIME)

        return driver

    def _init_pages(self):
        self.__driver.get(self.__naver_path)
        # 기기별 전체 선택
        self.__driver.find_element_by_xpath(NaverXpath.all_device_chkbox).click()
        # 성별 전체 선택
        self.__driver.find_element_by_xpath(NaverXpath.both_gender_chkbox).click()
        # 연령별 전체 선택
        self.__driver.find_element_by_xpath(NaverXpath.all_age_chkbox).click()

        self.__driver.execute_script(f'window.open("{self.__coupang_path}");')

        tabs = {'naver': self.__driver.window_handles[0], 'coupang': self.__driver.window_handles[1]}
        self.__driver.switch_to.window(tabs['naver'])
        return tabs

    def check_exists_by_xpath(self, xpath, waiting_time=0.2) -> bool:
        self.__driver.implicitly_wait(waiting_time)
        try:
            self.__driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        finally:
            self.__driver.implicitly_wait(self.__WAIT_TIME)
        return True

    def get_number_of_products_from_coupang(self, keyword: str) -> int:
        self._clear_searchbox(CoupangXpath.search_box)
        self._search(CoupangXpath.search_box)
        if self.check_exists_by_xpath(CoupangXpath.number_of_items):
            text = self.__driver.find_element_by_xpath(CoupangXpath.number_of_items).text.replace(',', '')
            return int(text)

        return -1

    def get_current_category(self) -> Category:
        last_combobox = 1

        for i in range(1, 4):
            if self.check_exists_by_xpath(NaverXpath.get_combobox(i)):
                last_combobox = i

        return Category(last_combobox)

    def get_current_category_list(self) -> [str]:
        category: Category = self.get_current_category()

        # open combobox
        self.__driver.find_element_by_xpath(NaverXpath.get_combobox(category.value)).click()

        elements = self.__driver.find_elements_by_xpath(NaverXpath.get_comboxbox_list(category.value))
        category_ls = []

        for element in elements:
            category_ls.append(element.text)

        # close combobox
        self.__driver.find_element_by_xpath(NaverXpath.get_combobox(category.value)).click()

        return category_ls

    def get_category_list(self, query_list: List[Tuple[Category, int]]) -> List[str]:
        sorted(query_list, key=lambda item: item[0].value)

        category_ls = []

        for t in query_list:
            self.__driver.find_element_by_xpath(NaverXpath.get_combobox(t[0].value)).click()
            self.__driver.find_element_by_xpath(NaverXpath.get_comboxbox_element(t[0].value, t[1]))

        # open combobox
        self.__driver.find_element_by_xpath(NaverXpath.get_comboxbox_list(query_list[-1][0].value)).click()
        elements = self.__driver.find_elements_by_xpath(NaverXpath.get_comboxbox_list(query_list[-1][0].value))
        category_ls = []

        for element in elements:
            category_ls.append(element.text)

        # close combobox
        self.__driver.find_element_by_xpath(NaverXpath.get_comboxbox_list(query_list[-1][0].value)).click()

        return category_ls

    def get_current_page_keywords(self, delay=1) -> List[str]:
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

    def _switch_to_coupang(self) -> None:
        self.__driver.switch_to.window(self.__tabs['coupang'])

    def _switch_to_naver(self) -> None:
        self.__driver.switch_to.window(self.__tabs['naver'])

    def _search(self, xpath: str, keyword: str) -> None:
        form = self.__driver.find_element_by_xpath(xpath)
        form.send_keys(keyword)
        form.submit()

    def _clear_searchbox(self, xpath: str) -> None:
        form = self.__driver.find_element_by_xpath(xpath)
        form.clear()

    def quit(self) -> None:
        self.__driver.quit()
