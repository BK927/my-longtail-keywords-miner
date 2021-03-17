import configparser


####Put your api keys in api_key.ini
# [NAVER ADS API]
# BASE_URL =
# API_KEY =
# SECRET_KEY =
# CUSTOMER_ID =

# [NAVER SEARCH API]
# CLIENT_ID =
# CLIENT_SECRET =


class ApiKeyReader:
    # NAVER ADS API
    BASE_URL = ''
    API_KEY = ''
    SECRET_KEY = ''
    CUSTOMER_ID = ''

    # NAVER SEARCH API
    CLIENT_ID = ''
    CLIENT_SECRET = ''

    def __init__(self):
        if self.BASE_URL:
            return

        config = configparser.ConfigParser()
        config.read('api_key.ini')

        self.BASE_URL = config['NAVER ADS API']['BASE_URL']
        self.API_KEY = config['NAVER ADS API']['API_KEY']
        self.SECRET_KEY = config['NAVER ADS API']['SECRET_KEY']
        self.CUSTOMER_ID = config['NAVER ADS API']['CUSTOMER_ID']

        self.CLIENT_ID = config['NAVER SEARCH API']['CLIENT_ID']
        self.CLIENT_SECRET = config['NAVER SEARCH API']['CLIENT_SECRET']
