from parsers.network_traffic import RequestSniffer
import requests
from typing import Dict, List
from .schemas import Product
import pickle
import os
from pathlib import Path


class CategoriesIterationState:

    def __init__(self):
        self._state_file_path = self._get_state_file_path()
        self.state = self._read_state_from_file()

    def _get_state_file_path(self) -> Path:
        module_dir = Path(__file__).parent  # Получаем абсолютный путь к директории текущего модуля
        return module_dir / "state.pickle"

    def _read_state_from_file(self) -> dict:
        if not os.path.exists(self._state_file_path):
            return {"i": 0}
        else:
            print('Parser will continue to execute using the "state.pickle" file')
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

    _host = "https://gippo-market.by"
    _api = "https://app.willesden.by/api/guest/shop"

    def __init__(self):
        print("Running <Spider gippo-market.by>")

        super().__init__()
        self._sniffer = RequestSniffer(headless=True)
        try:
            print("Intercept cookies & headers -> start")

            self._session = self._get_request_session()

            print("Intercept cookies & headers -> done")
        except Exception as _ex:
            print("Intercept cookies & headers -> error!")
            raise _ex

    def _get_headers(self) -> Dict:

        request_details = self._sniffer.fetch_request_details(url=f'{self._host}/')
        headers = {}
        for item in request_details:
            if item['request_headers'].get('baggage', None):
                headers = item['request_headers']

        return headers

    def _get_request_session(self) -> requests.Session:
        session = requests.Session()
        headers_dict = self._get_headers()
        session.headers.update(headers_dict)
        return session

    def _get_json_response(self, url, host=True) -> dict or list:
        response = self._session.get(self._api + url if host else url)
        if response.status_code != 200:
            raise ValueError(f'for url > {url} status_code == {response.status_code}')
        return response.json()

    def get_categories(self) -> List[Dict]:
        r = self._get_json_response('/categories')
        return r

    def collect_products(self, slug, url=None, products=None):
        if not url:
            url = self._api + "/products?page=1"
        if not products:
            products = []
        response: dict = self._get_json_response(url=f"{url}&filter[categories][slug]={slug}&market_id=73", host=False)
        [products.append(item_) for item_ in response['data']]
        url = response['links']['next']
        if not url:
            return products
        return self. collect_products(slug=slug, url=url, products=products)

    def get_product_details(self, product_id, category_id):
        url = f"/products/{product_id}?category_id={category_id}&market_id=73"
        response: dict = self._get_json_response(url=url, host=True)
        return response

    @staticmethod
    def cut_categories(categories) -> List[dict]:
        # Метод режет список с категориями до главных категорий (у которох общий родитель slug: vse)
        main_categories = []
        parent_category_id = None
        for category_item in categories:
            if not parent_category_id:
                if not category_item['parent_id'] and category_item['slug'] == "vse":
                    parent_category_id = category_item['id']
                continue
            if category_item['parent_id'] == parent_category_id:
                main_categories.append(category_item)
        return main_categories

    def crawl(self):
        try:
            print(f"Get all categories on {self._host} -> start")
            categories: List[dict] = self.get_categories()
            main_categories: List[dict] = self.cut_categories(categories)  # По этим категориям происходит итерация и запрос на получение товаров
            # Тут ключи - id категорий, значение - словаь объектов категории
            categories_article_hash: dict = {i['id']: {'name': i['title'], 'slug': i['slug'], 'parent_id': i['parent_id']}
                                     for i in categories}  # {id: {name: v, slug: v, parent_id:v}, id: {...}, ...}
            categories_slug_hash: dict = {i['slug']: i['id'] for i in categories}

        except Exception as _ex:
            print(f"Get all categories -> error! {_ex}")
            raise _ex

        try:
            start_i = self.state['i']  # загружаем состояние обхода списка категорий из файла pickle
        except Exception as _ex:
            start_i = 0

        for i in range(start_i, len(main_categories)):
            self.state['i'] = i
            self.write_state_2_file()  # # записываем состояние обхода списка категорий в файл pickle
            category_item = main_categories[i]
            category_id = category_item['id']

            print(f"Collect products {category_item['title']} -> start")
            products = self.collect_products(category_item['slug'])
            print(f"Collect products -> done")

            for product_item in products:
                product_details = self.get_product_details(product_item['id'], category_id)
                schemas_product_details = Product(**product_details)
                # Добавляем в schemas_product_details.categories главную родительскую категорию первого уровня
                # если её там нет
                schemas_product_details.add_main_category(category_title=category_item['title'],
                                                          category_slug=category_item['slug'])
                # Добавляем значения в parent_name (имя родительской категории). На текущий момент этот аттрибут none
                #
                for j in range(len(schemas_product_details.categories)):
                    if schemas_product_details.categories[j].title is None:  # Если в документе нет поля
                        schemas_product_details.categories[j].title = category_item['title']
                        continue
                    try:
                        category_article = categories_slug_hash[schemas_product_details.categories[j].slug]
                    except KeyError:
                        continue
                    parent_article = categories_article_hash[category_article]['parent_id']
                    parent_name = categories_article_hash[parent_article]['name']
                    if parent_name == 'Все':
                        parent_name = None
                    schemas_product_details.categories[j].parent_title = parent_name

                yield schemas_product_details
        try:
            os.remove(self._state_file_path)
        except Exception as _ex:
            print(_ex)

