from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from database import models
from database.database import get_db, SessionLocal
from typing import Optional
from langchain.tools import tool

@tool
def search_products(keywords: list[str], max_price: Optional[float] = None, is_organic: Optional[bool] = None) -> list[dict]:
    """
    Search for products from database based on a given query, max_price and is_organic

    Args:
        query(list[str]): List of keywords to search for a product.
        max_price(Optional[float]): The maximum price for a product.
        is_organic(Optional[int]): Whether to filter organic products or not.
    
    Returns:
        List[dict]: A list of all related products
    """

    with SessionLocal() as db:
        statement = select(models.Products)
        conditions = []
        for keyword in keywords:

            conditions.append(
                models.Products.name.ilike(f"%{keyword}%") 
                | models.Products.category.ilike(f"%{keyword}%")
            )

        if conditions:
            statement = statement.where(or_(*conditions))

        if max_price is not None:
            statement = statement.where(
                models.Products.price <= max_price
            )

        if is_organic is not None:
            bool = 0
            if is_organic:
                bool = 1
            statement = statement.where(
                models.Products.is_organic == bool
            )

        products = db.scalars(statement).all()

        return [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "description": product.description,
            }
            for product in products
        ]