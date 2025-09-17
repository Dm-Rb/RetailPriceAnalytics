from parsers.network_traffic import RequestSniffer
import parsers.edostavka_by.schemas as schemas
import requests
from typing import Dict
from bs4 import BeautifulSoup
import pickle
import os
import json
from pathlib import Path
from typing import Iterator


class CategoriesIterationState:

    def __init__(self):
        self._state_file_path = self._get_state_file_path()
        self.state = self._read_state_from_file()

    def _get_state_file_path(self) -> Path:
        module_dir = Path(__file__).parent  # Получаем абсолютный путь к директории текущего модуля
        return module_dir / "state.pickle"

    def _read_state_from_file(self) -> dict:
        if not os.path.exists(self._state_file_path):
            return {"i": 0, "j": 0}
        else:
            print('EdostavkaParser will continue to execute using the "state.pickle" file')
            input('Press Enter to continue... ')
            with open(self._state_file_path, 'rb') as f:
                return pickle.load(f)

    def write_state_2_file(self) -> bool:
        with open(self._state_file_path, 'wb') as f:
            pickle.dump(self.state, f)
            return True

    def delete_state_file(self) -> None:
        os.remove(self._state_file_path)


class Spider(CategoriesIterationState):

    _host = "https://edostavka.by"
    _api = "https://api2.edostavka.by/api/v2"

    def __init__(self):
        print("Running <Spider edostavka.by>")

        super().__init__()
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

    def _get_html_response(self, url, host=True) -> str:
        response = self._session.get(self._host + url if host else url)
        if response.status_code != 200:
            raise ValueError(f'for url > {url} status_code == {response.status_code}')
        return response.text

    def _get_json_response(self, endpoint) -> dict:
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'apiToken': self._session.cookies.get('apiToken', None),
            'Content-Type': 'application/json',
            'User-Agent': 'SiteEdostavka/1.0.0',
            'Web-User-Agent': 'SiteEdostavka/1.0.0'
        }
        response = requests.get(url=self._api + endpoint, headers=headers)
        return response.json()

    def get_categories(self) -> list[dict]:
        categories = []
        html = self._get_html_response("/categories")
        soup = BeautifulSoup(html, 'html.parser')
        for div in soup.find_all('div', class_='categories_subcategory__9qDc_'):
            a = div.find('a', class_='categories_subcategory__title__ViURP')
            category = {
                'name': a.text,
                'parent_category': None,
                'url': a['href'],
                'subcategories': []
            }
            for li in div.find_all('li', class_='categories_subcategory__item__0DeQO'):
                a = li.find('a', class_='categories_subcategory__link__joHdl')
                sub_category = {
                    'name': a.text,
                    'parent_category': category['name'],
                    'url': a['href'],
                    'subcategories': []
                }
                category['subcategories'].append(sub_category)
            categories.append(category)
        # example <categories>: [{category, subcategories[]}, {...} ]
        return categories

    def _extract_page_props(self, url) -> dict:
        html: str = self._get_html_response(url)
        soup = BeautifulSoup(html, 'html.parser')
        script_tag: soup = soup.find('script', id='__NEXT_DATA__')
        json_data: str = script_tag.string
        data: json = json.loads(json_data)
        return data

    def collect_products(self, url, pagination=None, products=None) -> list:
        if products is None:
            products = []

        json_data: dict = self._extract_page_props(url + pagination if pagination else url)
        json_data_listing = json_data["props"]["pageProps"]["listing"]
        product_listing = schemas.ProductListing(**json_data_listing)
        products.extend(product_listing.products)
        # The base case of recursion
        if product_listing.pageNumber >= product_listing.pageAmount:
            # product_listing.products = products
            return products
        pagination = f"?page={str(product_listing.pageNumber + 1)}"
        return self.collect_products(url, pagination, products)

    def get_product_details(self, product_id: int) -> schemas.Product or None:
        json_response = self._get_json_response(f"/product/{str(product_id)}")
        if json_response.get('product', None):
            product_details = schemas.Product(**json_response['product'])
            return product_details

    def crawl(self) -> Iterator[schemas.Product]:
        #Собраем все категории с сайта. Список списков, где главная категория со списком субкатегорий
        try:
            print(f"Get all categories on {self._host}/categories -> start")

            categories = self.get_categories()
            print(f"Get all categories -> done")
        except Exception as _ex:
            print("Get all categories on {self._host} -> error!")
            raise _ex

        try:
            start_i = self.state['i']  # загружаем состояние обхода списка категорий из файла pickle
        except Exception as _ex:
            start_i = 0
        # Итерируемся по главным категориям
        for i in range(start_i, len(categories)):
            self.state['i'] = i
            self.write_state_2_file()  # # записываем состояние обхода списка категорий в файл pickle
            category = categories[i]

            try:
                start_j = self.state['j']
            except Exception as _ex:
                start_j = 0

            # Итерируемся по субкатегориям главной категории categories[i]
            for j in range(start_j, len(category['subcategories'])):
                self.state['j'] = j
                subcategory = category['subcategories'][j]
                try:
                    print(f"Collect products  on {self._host}{subcategory['url']} -> start")
                    product_listing = self.collect_products(subcategory['url'])
                    print(f"Collect products -> done")
                except Exception as _ex:
                    print(f"Collect products on {self._host}{subcategory['url']} -> error!")
                    raise _ex

                ###
                for schemas_product in product_listing:
                    schemas_product_details = self.get_product_details(int(schemas_product.productId))
                    yield schemas_product_details

            self.state['j'] = 0
        try:
            os.remove(self._state_file_path)
        except Exception as _ex:
            print(_ex)

# if __name__ == "__main__": # example
#     spider = Spider()
#     for item in spider.crawl():
#         print(item)
#         input()
