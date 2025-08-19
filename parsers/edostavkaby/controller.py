from parsers.edostavkaby.spider_sync import Spider


def main():

    spider = Spider()
    categories = spider.get_categories()
    try:
        start_i = spider.state['i']
    except Exception as _ex:
        start_i = 0
    for i in range(start_i, len(categories)):
        spider.state['i'] = i
        spider.write_state_2_file()
        category = categories[i]

        try:
            start_j = spider.state['j']
        except Exception as _ex:
            start_j = 0
        for j in range(start_j, len(category['subcategories'])):
            spider.state['j'] = j
            spider.write_state_2_file()

            subcategory = category['subcategories'][j]
            print(subcategory['name'])
            # json_data = spider.extract_page_props(subcategory['url'])
            product_listing = spider.collect_products(subcategory['url'])
            # Тут необходимо развернуть логику проверки значения в базе данных. Если товар есть в Бд - обновить цену.
            # Если нет - передать айдишник в список для асинхронного парсинга подробностей товара
            for item in product_listing:
                product_details = spider.get_product_details(int(item.productId))
                print(product_details)
            input('next...')








    # print(spider.state)
    # print(categories)
    # json_data = spider.extract_page_props("/product/47049")
    # # products_data = json_data["props"]["pageProps"]["listing"]
    # product_data = json_data["props"]["pageProps"]["productData"]
    # parsed = ProductListing(**product_data)
    # print(json_data)


