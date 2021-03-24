import pickle
import time

from typing import Tuple

from crawler.base_driver import BaseDriver
from crawler.xpath_container import NaverXpath


class NaverCacheDriver(BaseDriver):
    _categories = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        cls = type(self)
        if not hasattr(cls, "_init"):
            cls._init = True
            super().__init__()
            self._init_page()
            self.try_to_load_cache()

    @staticmethod
    def encode(index: Tuple[int, int, int, int]) -> str:
        code = ''
        for i in range(4):
            if index[i] == 0:
                break
            code += NaverCacheDriver._generate_single_field(i + 1, index[i])
        return code

    @staticmethod
    def decode(category_code: str) -> tuple:
        category_ls = []
        index_ls = []
        count = int(len(category_code) / 3)
        for i in range(count):
            code = category_code[i * 3:(i + 1) * 3 - 1]
            category_ls.append(Category(int(code[0])))
            index_ls.append(int(code[1:]))

        return tuple(index_ls)

    @staticmethod
    def convert_to_current_depth(index: Tuple[int, int, int, int]) -> int:
        position = NaverCacheDriver.convert_to_current_position(index)
        return position[0]

    @staticmethod
    def convert_to_current_position(index: Tuple[int, int, int, int]) -> tuple:
        depth = 0
        last_index = 0
        for i in range(4):
            if index[i] == 0:
                break
            last_index = index[i]
            depth += 1
        return depth, last_index

    def get_category_name(self, index: Tuple[int, int, int, int]) -> str:
        code = NaverCacheDriver.encode(index)
        return NaverCacheDriver._categories[code]

    def get_next_category_list(self, index: Tuple[int, int, int, int]) -> list:
        depth = NaverCacheDriver.convert_to_current_depth(index)
        if depth > 3:
            return []

        code = NaverCacheDriver.encode(index)
        index_ls = list(index)
        ls = []

        if code == '':
            for i in range(1, 20):
                query = NaverCacheDriver.encode((i, 0, 0, 0))
                if query in NaverCacheDriver._categories:
                    ls.append(NaverCacheDriver._categories[query])
                else:
                    return ls

        for i in range(1, 20):
            index_ls[depth] += 1
            query = NaverCacheDriver.encode(list(index_ls))
            if query in NaverCacheDriver._categories:
                ls.append(NaverCacheDriver._categories[query])
            else:
                break
        return ls

    def get_number_of_next_category(self, index: Tuple[int, int, int, int]) -> int:
        depth = NaverCacheDriver.convert_to_current_depth(index)
        if depth > 3:
            return 0

        code = NaverCacheDriver.encode(index)
        index_ls = list(index)
        count = 0

        if code == '':
            for i in range(1, 20):
                query = NaverCacheDriver.encode((i, 0, 0, 0))
                if query in NaverCacheDriver._categories:
                    count = i
                else:
                    return count

        for i in range(1, 20):
            index_ls[depth] += 1
            query = NaverCacheDriver.encode(list(index_ls))
            if query in NaverCacheDriver._categories:
                count = i
            else:
                return count

    # formula : category index + element index + ...
    def try_to_load_cache(self) -> bool:
        try:
            with open('cache', 'rb') as file:
                NaverCacheDriver._categories = pickle.load(file)
        except FileNotFoundError:
            return False

        return True

    def update_file(self, delay: float) -> None:
        ls = [1]
        code = ''
        categories = {}

        self._update_recursive(1, '', delay, categories)
        categories = NaverCacheDriver._categories

        with open('cache', 'wb') as file:
            pickle.dump(NaverCacheDriver._categories, file)

    def _update_recursive(self, depth: int, code: str, delay: float, category_dic: dict):
        if not self.check_exists_by_xpath(NaverXpath.get_combobox(depth)):
            return

        self._driver.find_element_by_xpath(NaverXpath.get_combobox(depth)).click()
        time.sleep(delay)
        elements = self._driver.find_elements_by_xpath(NaverXpath.get_comboxbox_list(depth))

        code += str(depth) + '00'

        for i in range(len(elements)):
            code = NaverCacheDriver._change_last_index(code, i + 1)
            category_dic[code] = elements[i].text
            print(f'{code}: {NaverCacheDriver._categories[code]}')

        code = code[0:len(code) - 3]
        self._driver.find_element_by_xpath(NaverXpath.get_combobox(depth)).click()

        if depth > 3:
            return

        for i in range(1, len(elements) + 1):
            code += NaverCacheDriver._generate_single_field(depth, i)
            self._driver.find_element_by_xpath(NaverXpath.get_combobox(depth)).click()
            self._driver.find_element_by_xpath(NaverXpath.get_comboxbox_element(depth, i)).click()
            self._update_recursive(depth + 1, code, delay, category_dic)
            code = code[0:len(code) - 3]

    def _init_page(self) -> None:
        self._driver.get(NaverXpath.url)

    def _save_category(self) -> None:
        with open('cache', 'wb') as file:
            pickle.dump(NaverCacheDriver._categories, file)

    @staticmethod
    def _generate_single_field(depth: int, index: int) -> str:
        return str(depth) + '{:0>2d}'.format(index)

    @staticmethod
    def _change_last_index(code: str, index: int) -> str:
        return code[0:len(code) - 2] + '{:0>2d}'.format(index)
