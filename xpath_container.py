class NaverXpath:
    url = 'https://datalab.naver.com/shoppingInsight/sCategory.naver'

    lookup_btn = '//*[@id="content"]/div[2]/div/div[1]/div/a'
    next_page_btn = '//*[@id="content"]/div[2]/div/div[2]/div[2]/div/div/div[2]/div/a[2]'
    all_device_chkbox = '//*[@id="18_device_0"]'
    both_gender_chkbox = '//*[@id="19_gender_0"]'
    all_age_chkbox = '//*[@id="20_age_0"]'

    @staticmethod
    def get_combobox(depth: int) -> str:
        return f'//*[@id="content"]/div[2]/div/div/div/div/div[1]/div/div[{depth}]/span'

    @staticmethod
    def get_combobox_title(depth: int) -> str:
        return f'//*[@id="content"]/div[2]/div/div[1]/div/div/div[1]/div/div[{depth}]/span'

    @staticmethod
    def get_comboxbox_list(depth: int) -> str:
        return f'//*[@id="content"]/div[2]/div/div/div/div/div[1]/div/div[{depth}]/ul/li'

    @staticmethod
    def get_comboxbox_element(depth: int, index: int) -> str:
        return f'//*[@id="content"]/div[2]/div/div/div/div/div[1]/div/div[{depth}]/ul/li[{index}]/a'

    @staticmethod
    def get_keyword(index: int) -> str:
        return f'//*[@id="content"]/div[2]/div/div[2]/div[2]/div/div/div[1]/ul/li[{index}]/a'


class CoupangXpath:
    url = 'https://www.coupang.com/'

    search_box = '//*[@id="headerSearchKeyword"]'
    search_btn = '//*[@id="headerSearchBtn"]'
    number_of_items = '//*[@id="searchOptionForm"]/div[2]/div[2]/div[1]/p/strong[2]'
