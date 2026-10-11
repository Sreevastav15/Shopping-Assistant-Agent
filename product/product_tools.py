from sqlalchemy import select, or_
from database import models
from database.database import SessionLocal
from typing import Optional
from langchain.tools import tool

@tool
def search_products(keywords: list[str], max_price: Optional[float] = None, is_organic: Optional[bool] = None) -> list[dict]:
    """
    Search for products from database based on a given query, max_price and is_organic

    Args:
        keywords(list[str]):list of search terms. Returns products matching ANY of the keywords. Pass all terms in a single call.t.
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

@tool
def search_product_id(ids: list[int]) -> list[dict]:
    """
    Get details of products by id.

    Args:
        ids(list[int]): List of products ids to search.
    Returns:
        list[dict]: List of all related products
    """

    with SessionLocal() as db:
        products = db.scalars(
            select(
                models.Products
            )
            .where(models.Products.id.in_(ids))
        ).all()

    return[
        {
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'price': product.price,
            'description': product.description
        } for product in products
    ]

@tool
def get_categories() -> list[str]:
    """
    Returns a list of unique categories of products available.

    Args:
        None
    Returns:
        list[str]: A list of all unique categories
    """
    
    with SessionLocal() as db:
        categories = db.scalars(
            select(models.Products.category)
            .distinct()
            .order_by(models.Products.category)
        ).all()

    return [str(category) for category in categories]