class Cache:
    def __init__(self):
        self.categories = {}        # category_name: database_id
        self.manufacturers = {}     # manufactory_name: database_id
        self.product_article = {}  # article: product_id
        self.properties = {}        # property_name: database_id