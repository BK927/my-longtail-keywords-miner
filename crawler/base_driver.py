import os
import platform
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from ini_reader import IniReader

try:
    from pyvirtualdisplay import Display
except:
    pass


class BaseDriver:
    # selenium crawler setting
    __driver_path = IniReader.DRIVER_PATH
    __service_log_path = "log/chromedriver.log"
    __service_args = ['--verbose']

    __WAIT_TIME = 4

    def __init__(self):
        self._display = None
        self._driver = self._init_driver()

    def __del__(self):
        self._driver.quit()
        if platform.system() == 'Linux':
            self._display.stop()

    def _init_driver(self) -> WebDriver:
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

        orig = None
        if platform.system() == 'Linux':
            orig = os.environ["DISPLAY"]
            self._display = Display(visible=False, size=(1920, 1080))
            self._display.start()

        driver = webdriver.Chrome(BaseDriver.__driver_path,
                                  service_args=BaseDriver.__service_args,
                                  service_log_path=BaseDriver.__service_log_path,
                                  chrome_options=options)

        if platform.system() == 'Linux':
            os.environ["DISPLAY"] = orig

        driver.implicitly_wait(self.__WAIT_TIME)

        return driver

    def check_exists_by_xpath(self, xpath, waiting_time=0.3) -> bool:
        self._driver.implicitly_wait(waiting_time)
        try:
            self._driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        finally:
            self._driver.implicitly_wait(self.__WAIT_TIME)
        return True

    def _get_text(self, xpath) -> str:
        return self._driver.find_element_by_xpath(xpath).text

    def _save_screenshot(self) -> None:
        self._driver.save_screenshot('./log/' + time.strftime('%c', time.localtime(time.time())) + '.png')

    def quit(self) -> None:
        self._driver.quit()
