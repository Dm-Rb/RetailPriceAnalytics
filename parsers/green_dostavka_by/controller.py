from parsers.green_dostavka_by.spider_sync import Spider
from database.session import get_session_factory
from parsers.service import CategoryService
from datetime import datetime as dt


def main():
    spider = Spider()
    session_factory = get_session_factory('catalog')
    service_data = CategoryService(session_factory=session_factory, source_name='green-dostavka.by')
    for product in spider.crawl():
        product_id = service_data.articles.get(str(product.article), None)
        if not product_id:
            # manufacturer
            manufacturer_id = service_data.get_manufactory_id(trademark=product.manufacturer_trademark,
                                                              full_name=product.manufacturer_name,
                                                              country=product.manufacturer_country)

            # product
            product_id = service_data.get_product_id(manufacturer_id=manufacturer_id,
                                                     name=product.name.strip(),
                                                     article=str(product.article),
                                                     barcode=product.barcode.strip() if product.barcode else None,
                                                     description=None,
                                                     unit=product.unit,
                                                     composition=product.composition,
                                                     storage_info=product.storage_info)
            # categories / product_category
            if product.categories_:
                categories_id_list = []
                for item in product.categories_:
                    for i, category in enumerate(item):
                        parent_name = item[i - 1] if i != 0 else None
                        category_id = service_data.get_category_id(category_name=category, parent_name=parent_name)
                        categories_id_list.append(category_id)
                # relationship product-category
                service_data.save_product_category_relations(product_id=product_id, categories_id=categories_id_list)

            # properties
            for property in product.properties:
                property_id = service_data.get_property_id(name=property.name,
                                                           group=property.group
                                                           )
                property_values_list = [property.value]
                # relationship product-property
                service_data.save_product_property_values_relations(product_id=product_id,
                                                                    property_id=property_id,
                                                                    values=property_values_list)

            # product_images
            service_data.save_product_images_relations(product_id=product_id,
                                                       image_urls_list=product.images)
        #
        if product.prices:
            service_data.save_product_price(product_id=product_id,
                                            price=float(product.prices.priceWithSale),
                                            date_time=str(dt.now().replace(microsecond=0)))

