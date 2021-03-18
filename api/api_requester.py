import logging
import time
import json
import requests
import urllib.request
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from api import signaturehelper
from ini_reader import *
from ezlogger import EzLogger


class NaverApi:
    MAX_RETRY = 20
    TIMEOUT = 10
    CODE429_WAIT_TIME = 2

    @staticmethod
    def get_header(method, uri, api_key, secret_key, customer_id):
        timestamp = str(round(time.time() * 1000))
        signature = signaturehelper.Signature.generate(timestamp, method, uri, secret_key)
        return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': api_key,
                'X-Customer': str(customer_id), 'X-Signature': signature}

    @staticmethod
    def get_monthly_qc_cnt(keyword):
        # Keywords Retrieve
        uri = '/keywordstool'
        method = 'GET'
        url = IniReader.BASE_URL + uri + f'?hintKeywords={keyword}&showDetail=1'

        response = None

        for tries in range(NaverApi.MAX_RETRY):
            try:
                # 질의 json->파이썬 객체로 파싱
                response = requests.get(url, headers=NaverApi.get_header(method, uri, IniReader.API_KEY,
                                                                         IniReader.SECRET_KEY,
                                                                         IniReader.CUSTOMER_ID), timeout=NaverApi.TIMEOUT)
            except Exception as e:
                EzLogger.logfile(logging.WARNING, str(e) + f',get_monthly_qc_cnt:{url}')
                if tries < (NaverApi.MAX_RETRY - 1):
                    time.sleep(NaverApi.CODE429_WAIT_TIME)
                    continue
                else:
                    EzLogger.logfile(logging.WARNING,
                                     f'Has tried {NaverApi.MAX_RETRY} times to access url {url}, all failed!')
                    return -1
            if int(response.status_code) == 200:
                break
            if int(response.status_code) == 429:
                EzLogger.logfile(logging.WARNING,
                                 f'keyword:{keyword} try:{tries} get_monthly_qc_cnt got {str(response.status_code)}')
                time.sleep(NaverApi.CODE429_WAIT_TIME)
                continue
            if not int(response.status_code) == 200:
                EzLogger.logfile(logging.WARNING,
                                 f'keyword:{keyword} try:{tries} get_monthly_qc_cnt got {str(response.status_code)}')
                time.sleep(0.5)
                continue

        if not int(response.status_code) == 200:
            EzLogger.logfile(logging.WARNING,
                             f'get_monthly_qc_cnt: Has tried {NaverApi.MAX_RETRY} times to access url {url}, but got {str(response.status_code)}')
            return -1

        # 원하는 키워드만 딕셔너리로 가져오기
        data = response.json()['keywordList'][0]

        pc_query_count = 0
        mobile_query_count = 0
        # 10보다 적으면 <10으로 표시되기 때문에 체크
        if not data['monthlyPcQcCnt'] == '< 10':
            pc_query_count = int(data['monthlyPcQcCnt'])

        if not data['monthlyMobileQcCnt'] == '< 10':
            mobile_query_count = int(data['monthlyMobileQcCnt'])

        # PC랑 모바일 검색수 합계
        return pc_query_count + mobile_query_count

    @staticmethod
    def get_quantity_of_items(keyword):
        encText = urllib.parse.quote(keyword)
        url = "https://openapi.naver.com/v1/search/shop.json?query=" + encText

        # 네이버 검색 API에 질의
        request = Request(url)
        request.add_header("X-Naver-Client-Id", IniReader.CLIENT_ID)
        request.add_header("X-Naver-Client-Secret", IniReader.CLIENT_SECRET)

        response = None

        for tries in range(NaverApi.MAX_RETRY):
            try:
                # 질의 json->파이썬 객체로 파싱
                response = urlopen(request, timeout=NaverApi.TIMEOUT)
            except Exception as e:
                EzLogger.logfile(logging.WARNING, str(e) + f',get_quantity_of_items:{url}')
                if tries < (NaverApi.MAX_RETRY - 1):
                    continue
                else:
                    EzLogger.logfile(logging.WARNING,
                                     f'Has tried {NaverApi.MAX_RETRY} times to access url {url}, all failed!')
                    return -1

            if int(response.getcode()) == 200:
                break
            if int(response.getcode()) == 429:
                EzLogger.logfile(logging.WARNING,
                                 f'keyword:{keyword} try:{tries} get_quantity_of_items got {str(response.getcode())}')
                time.sleep(NaverApi.CODE429_WAIT_TIME)
                continue
            if not int(response.getcode()) == 200:
                EzLogger.logfile(logging.WARNING,
                                 f'keyword:{keyword} try:{tries} get_quantity_of_items got {str(response.getcode())}')
                time.sleep(0.5)
                continue

        if not int(response.getcode()) == 200:
            EzLogger.logfile(logging.WARNING,
                             f'get_quantity_of_items: Has tried {NaverApi.MAX_RETRY} times to access url {url}, but got {str(response.getcode())}')
            return -1

        return json.loads(response.read().decode('utf-8'))['total']
