class Cache:
    def __init__(self):
        self.sources = {}           # source_name: database_id
        self.categories = {}        # category_name: database_id
        self.manufacturers = {}     # manufactory_name: database_id
        self.articles = {}          # article: product_id
        self.properties = {}        # property_name: database_id