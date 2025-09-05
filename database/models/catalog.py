from sqlalchemy import Integer, String, Column, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from .base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category",
                         remote_side=[id],
                         backref="subcategories",
                         foreign_keys=[parent_id])  # Добавляем foreign_keys

    product_category = relationship('ProductCategory', back_populates='category')

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', parent_id='{self.parent_id}')>"


class Manufactory(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trademark = Column(String(100), nullable=True)
    full_name = Column(String(300), nullable=False)
    country = Column(String(52), nullable=True)

    product = relationship("Product", back_populates="manufacturer",
                          lazy="dynamic")  # lazy="dynamic" для фильтрации

    def __repr__(self):
        return f"<Manufactory(id={self.id}, trademark='{self.trademark}', " \
               f"full_name='{self.full_name}, country='{self.country}')>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    barcode = Column(String(14), nullable=True)
    description = Column(Text, nullable=True)
    composition = Column(Text, nullable=True)
    storage_info = Column(Text, nullable=True)
    unit = Column(String(15), nullable=True)

    manufacturer = relationship("Manufactory", back_populates="product")
    product_category = relationship("ProductCategory", back_populates="product")
    product_display = relationship("ProductDisplay", back_populates="product")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    group = Column(String(255), nullable=True)


class ProductCategory(Base):
    __tablename__ = "relations_product_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))

    product = relationship("Product", back_populates="product_category")
    category = relationship("Category", back_populates="product_category")


class ProductDisplay(Base):
    """
    Таблица связей. Содержит название артикула товара.
    Артикула в разных источниках разные для одного  и того же товара, в связи с этим имеется эта таблица
    """
    __tablename__ = "relations_product_display"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(35), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    article = Column(String(35), nullable=True)

    product = relationship("Product", back_populates="product_display")


class ProductPropertyValue(Base):
    """
    Таблица связей. Содержит название артикула товара.
    Артикула в разных источниках разные для одного  и того же товара, в связи с этим имеется эта таблица
    """
    __tablename__ = "relations_product_property"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    value = Column(Text, nullable=True)

    product = relationship("Product")
    property = relationship("Property")


class ProductImage(Base):
    __tablename__ = "relations_product_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String(300), nullable=False)

    product = relationship("Product")


class ProductPrice(Base):
    __tablename__ = "relations_product_price"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_display_id = Column(Integer, ForeignKey("relations_product_display.id"), nullable=False)
    price = Column(Numeric(10, 2))
    date_time = Column(DateTime, nullable=False)

    product_display = relationship("ProductDisplay")

