from sqlalchemy import create_engine, MetaData, Table, Integer, String, Column, DateTime, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Category(Base):
    """Категории"""
    __tablename__ = "categories"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    parent_id = Column(Integer, ForeignKey("catalog.categories.id"), nullable=True)

    # Связи
    parent = relationship("Category", remote_side=[id], backref="subcategories")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Manufactory(Base):
    """Производитель"""
    __tablename__ = "manufacturers"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    trademark = Column(String(100), nullable=False)
    full_name = Column(String(300), nullable=True)
    country = Column(String(52))


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

    manufacturer = relationship("Manufactory", back_populates="products")


#     # Связи
#     category = relationship(#     "Category", backref="products")
#     prices = relationship("HistoricalPrice", back_populates="product")

