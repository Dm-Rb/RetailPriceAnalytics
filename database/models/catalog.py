from sqlalchemy import Integer, String, Column, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from .base import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    parent_id = Column(Integer, ForeignKey("catalog.categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id], backref="subcategories")
    product_category = relationship('ProductCategory', back_populates='category')

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', parent_id='{self.parent_id}')>"


class Manufactory(Base):
    __tablename__ = "manufacturers"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    trademark = Column(String(100), nullable=False)
    full_name = Column(String(300), nullable=True)
    country = Column(String(52))

    product = relationship("Product", back_populates="manufacturer",
                          lazy="dynamic")  # lazy="dynamic" для фильтрации

    def __repr__(self):
        return f"<Manufactory(id={self.id}, trademark='{self.trademark}', " \
               f"full_name='{self.full_name}, country='{self.country}')>"


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_id = Column(Integer, ForeignKey("catalog.manufacturers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    barcode = Column(String(14), nullable=True)
    description = Column(String(350), nullable=True)
    composition = Column(String(500), nullable=True)
    storage_info = Column(String(350), nullable=True)
    unit = Column(String(15), nullable=True)

    manufacturer = relationship("Manufactory", back_populates="product")
    product_category = relationship("ProductCategory", back_populates="product")
    product_display = relationship("ProductDisplay", back_populates="product")


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    group = Column(String(255), nullable=True)


class ProductCategory(Base):
    __tablename__ = "relations_product_category"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("catalog.products.id"), nullable=False)
    category_id = Column(Integer, ForeignKey('catalog.categories.id'))

    product = relationship("Product", back_populates="product_category")
    category = relationship("Category", back_populates="product_category")


class ProductDisplay(Base):
    """
    Таблица связей. Содержит название артикула товара.
    Артикула в разных источниках разные для одного  и того же товара, в связи с этим имеется эта таблица
    """
    __tablename__ = "relations_product_display"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(35), nullable=False)
    product_id = Column(Integer, ForeignKey("catalog.products.id"), nullable=False)
    article = Column(String(35), nullable=True)

    product = relationship("Product", back_populates="product_display")


class ProductPropertyValue(Base):
    """
    Таблица связей. Содержит название артикула товара.
    Артикула в разных источниках разные для одного  и того же товара, в связи с этим имеется эта таблица
    """
    __tablename__ = "relations_product_property"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("catalog.products.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("catalog.properties.id"), nullable=False)
    value = Column(String(250), nullable=True)

    product = relationship("Product")
    property = relationship("Property")


class ProductPrice(Base):
    __tablename__ = "relations_product_price"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_display_id = Column(Integer, ForeignKey("catalog.relations_product_display.id"), nullable=False)
    price = Column(Numeric(10, 2))
    date_time = Column(DateTime, nullable=False)

    product_display = relationship("ProductDisplay")

