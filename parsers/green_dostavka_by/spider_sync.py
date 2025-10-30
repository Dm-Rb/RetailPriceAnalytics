import requests
from bs4 import BeautifulSoup
from parsers.network_traffic import RequestSniffer
from typing import Dict, List
import json
from parsers.green_dostavka_by.schemas import Categories
from parsers.green_dostavka_by.schemas import Product


class Spider():

    _host = "https://green-dostavka.by"
    _api = None
    STOREID = "21"  # CONSTANTA

    def __init__(self):
        print("Running <Spider green-dostavka.by>")

        # super().__init__()
        self._sniffer = RequestSniffer(headless=True)
        try:
            print("Intercept cookies & headers -> start")

            self._session = self._get_request_session()

            print("Intercept cookies & headers -> done")
        except Exception as _ex:
            print("Intercept cookies & headers -> error!")
            raise _ex

    def _get_headers_cookies(self) -> Dict:

        request_details = self._sniffer.fetch_request_details(url=f'{self._host}/')

        request_details = [i for i in request_details if i['url'] == f'{self._host}/']
        if not request_details:
            raise ValueError('<request_details> is empty')
        headers = request_details[0]['request_headers']
        cookies = {x['name']: x['value'] for x in request_details[0]['cookies']}
        self._sniffer = None

        return {'headers': headers, 'cookies': cookies}

    def _get_request_session(self) -> requests.Session:
        session = requests.Session()
        headers_cookies_dict = self._get_headers_cookies()
        session.headers.update(headers_cookies_dict['headers'])
        session.cookies.update(headers_cookies_dict['cookies'])
        return session

    def get_response(self, url, host=True, json_=False) -> str or dict:
        response = self._session.get(self._host + url if host else url)
        if response.status_code != 200:
            raise ValueError(f'for url > {url} status_code == {response.status_code}')
        if json_:
            return response.json()
        return response.text

    def get_categories_schema(self):
        text_ = self.get_response(url="/catalog/")
        # json вшит прямо в текст документа. парсим его и сериализуем как json
        soup = BeautifulSoup(text_, 'html.parser')
        data_text = soup.find('script', id='__NEXT_DATA__').text
        data_json = json.loads(data_text)
        categories = Categories(**data_json)
        return categories

    def collect_products_by_category(self, categoryId:int , skip=0, data=None) -> List:
        if not data:
            data = []
        LIMIT = 100  # CONSTANTA
        end_point = f"/api/v1/products?storeId={self.STOREID}&categoryId={str(categoryId)}&limit={str(LIMIT)}&skip={str(skip)}"
        resp: dict = self.get_response(url=end_point, json_=True)
        resp_count = resp.get('count', 0)
        data.extend(resp.get('items', []))
        if resp_count < LIMIT + skip:
            return data
        else:
            return self.collect_products_by_category(categoryId, skip+100, data)

    def get_product_details(self, product_slug):
        end_point = f"/api/v1/products/{product_slug}?storeId={self.STOREID}"
        resp: dict = self.get_response(url=end_point, json_=True)
        return resp

    def crawl(self):
        categories = self.get_categories_schema()
        print(f"Get all categories on {self._host} -> start")

        for category_item in categories.categories:
            if category_item.parentId:
                continue
            if category_item.productsViewType != "NORMAL":
                continue
            print(f"Collect products on {category_item.name}")
            products = self.collect_products_by_category(category_item.id)
            print(f"Collect products done")
            for item in products:
                product_slug = item.get('slug', None)
                if not product_slug:
                    continue
                try:
                    product_details = self.get_product_details(product_slug)
                    product_schema = Product(**product_details)
                    product_schema.set_categories(categories)  # product_schema.categories - двухмерный список
                    yield product_schema
                except Exception as ex:
                    print(ex)
                    continue
