from sqlalchemy import Integer, String, Column, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from .base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)

    # relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    source = relationship("Source", back_populates="categories")
    product_category = relationship("ProductCategory", back_populates="category")  # исправлено на category


class Manufactory(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trademark = Column(String(100), nullable=True)
    full_name = Column(String(300), nullable=True)
    country = Column(String(52), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)

    # relationships
    source = relationship("Source", back_populates="manufacturers")
    product = relationship("Product", back_populates="manufacturer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    name = Column(String(255), nullable=False)
    barcode = Column(String(14), nullable=True)
    description = Column(Text, nullable=True)
    composition = Column(Text, nullable=True)
    storage_info = Column(Text, nullable=True)
    unit = Column(String(15), nullable=True)
    source_article = Column(String(60), nullable=True)

    # relationships
    source = relationship("Source", back_populates="product")
    manufacturer = relationship("Manufactory", back_populates="product")  # исправлено на Manufactory
    product_category = relationship("ProductCategory", back_populates="product")  # исправлено на product
    property_value = relationship("ProductPropertyValue", back_populates="product")  # исправлено на product
    image = relationship("ProductImage", back_populates="product")  # исправлено на product
    price = relationship("ProductPrice", back_populates="product")  # исправлено на product


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(40), nullable=False)

    # relationships
    categories = relationship("Category", back_populates="source")
    manufacturers = relationship("Manufactory", back_populates="source")  # исправлено на Manufactory
    product = relationship("Product", back_populates="source")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    group = Column(String(255), nullable=True)

    # relationships
    property_value = relationship("ProductPropertyValue", back_populates="property")  # исправлено на property


class ProductCategory(Base):
    __tablename__ = "relations_product_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # relationships
    product = relationship("Product", back_populates="product_category")  # исправлено на product
    category = relationship("Category", back_populates="product_category")  # исправлено на category


class ProductPropertyValue(Base):
    __tablename__ = "relations_product_property"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    value = Column(Text, nullable=True)

    # relationships
    product = relationship("Product", back_populates="property_value")  # исправлено на product
    property = relationship("Property", back_populates="property_value")  # исправлено на property


class ProductImage(Base):
    __tablename__ = "relations_product_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String(300), nullable=False)

    # relationships
    product = relationship("Product", back_populates="image")


class ProductPrice(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Numeric(10, 2))
    date_time = Column(DateTime, nullable=False)

    # relationships
    product = relationship("Product", back_populates="price")  # исправлено на product