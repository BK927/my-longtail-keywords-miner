# My longtail keywords miner
A crossplatform crawler for Naver storefarm service, Coupang and Enuri.

## Mendatory
Before using this program, you have to get Naver api licenses.</br>
You can find the license at the links below.</br>
https://searchad.naver.com/</br>
https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md#%EC%87%BC%ED%95%91</br>
And also you have to download chromedriver</br>
https://chromedriver.chromium.org/</br>

## api_key.ini
The program will get api keys from <b>api_key.ini</b>.<br>
Fill api_key.ini like below example</br></br>
### [NAVER ADS API]</br>
BASE_URL = </br>
API_KEY = </br>
SECRET_KEY = </br>
CUSTOMER_ID = </br>
</br>
### [NAVER SEARCH API]</br>
CLIENT_ID = </br>
CLIENT_SECRET = </br>
### [DRIVER]</br>
DRIVER_PATH = C:\chromedriver</br>
HEADLESS = TRUE</br>

## Usage
Crawled datas will be saved in Excel file(*.xlxs)</br>
You can specify a path and file name before you save.</br>
Coupang and Enuri don't provide api and allow crawling bot. So those options gonna take much longer time than no option.
