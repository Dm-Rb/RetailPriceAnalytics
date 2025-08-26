from spider_sync import Spider
from cache.parsers.edostavkaby.cache import Cache
from database.crud.catalog import CatalogCRUD
from database.session import get_session_factory

def main():
    spider = Spider()
    cache = Cache()
    database = CatalogCRUD()
    for product in spider.crawl():
        if product.categories:
            for category in product.categories:
                if cache.categories.get(category, None):


        print(product)
        input()

if __name__ == "__main__":
    main()
