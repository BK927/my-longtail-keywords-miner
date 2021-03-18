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


class IniReader:
    __config = configparser.ConfigParser()
    __config.read('configure.ini')

    # NAVER ADS API
    BASE_URL = __config['NAVER ADS API']['BASE_URL']
    API_KEY = __config['NAVER ADS API']['API_KEY']
    SECRET_KEY = __config['NAVER ADS API']['SECRET_KEY']
    CUSTOMER_ID = __config['NAVER ADS API']['CUSTOMER_ID']

    # NAVER SEARCH API
    CLIENT_ID = __config['NAVER SEARCH API']['CLIENT_ID']
    CLIENT_SECRET = __config['NAVER SEARCH API']['CLIENT_SECRET']

    # Chromedriver
    DRIVER_PATH = __config['DRIVER']['DRIVER_PATH']
    HEADLESS = __config['DRIVER']['HEADLESS']
    NO_SANDBOX = __config['DRIVER']['NO_SANDBOX']
