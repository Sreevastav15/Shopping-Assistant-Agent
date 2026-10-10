from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Float, ForeignKey
from database.database import Base

class Products(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    is_organic: Mapped[int] = mapped_column(Integer, default=0)

class Reviews(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable= False)
    rating: Mapped[float] = mapped_column(Float)
    reviewer_name: Mapped[str] = mapped_column(Text)
    review_text: Mapped[str] = mapped_column(Text)
