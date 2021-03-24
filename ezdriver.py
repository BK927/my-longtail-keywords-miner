import platform

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

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
            display = Display(visible=False, size=(1920, 1080))
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

    def check_exists_by_xpath(self, xpath):
        self.__driver.implicitly_wait(0.2)
        try:
            self.__driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        finally:
            self.__driver.implicitly_wait(self.__WAIT_TIME)
        return True

    def switch_to_coupang(self):
        self.__driver.switch_to.window(self.__tabs['coupang'])

    def switch_to_naver(self):
        self.__driver.switch_to.window(self.__tabs['naver'])

    def search(self, xpath: str, keyword: str):
        form = self.__driver.find_element_by_xpath(xpath)
        form.send_keys(keyword)
        form.submit()

    def clear_searchbox(self, xpath: str) -> None:
        form = self.__driver.find_element_by_xpath(xpath)
        form.clear()

    def click(self, xpath):
        self.__driver.find_element_by_xpath(xpath).click()

    def get_text(self, xpath):
        ignored_exceptions = (StaleElementReferenceException,)
        raw = WebDriverWait(self.__driver, 3, ignored_exceptions=ignored_exceptions) \
            .until(expected_conditions.presence_of_element_located((By.XPATH, xpath)))
        return raw.text

    def find_elements(self, xpath):
        return self.__driver.find_elements_by_xpath(xpath)

    def quit(self):
        self.__driver.quit()
