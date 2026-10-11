from sqlalchemy import select, func, or_
from database import models
from database.database import SessionLocal
from typing import Optional
from langchain.tools import tool

@tool
def get_product_reviews(product_ids: list[int]) -> dict:
    """
    Get average customer rating, total rating count and the reviews of a product.

    Args:
        product_ids(list[int]): A list of product_ids of products to get reviews and ratings
    Returns:
        dict: {"product_id": {"rating": float, "rating_count": int, "review": text}} 
    """

    with SessionLocal() as db:
        rows = db.execute(
            select(
                models.Reviews.product_id,
                func.avg(models.Reviews.rating).label("average_rating"),
                func.count(models.Reviews.id).label("rating_count"),
                func.string_agg(models.Reviews.review_text, " ").label("reviews")
                )
                .where(
                models.Reviews.product_id.in_(product_ids)
            ).group_by(models.Reviews.product_id)).all()
    return {
        row.product_id:{
            'rating': float(row.average_rating) or None,
            'rating_count':int(row.rating_count) or None,
            'review': row.reviews or ""
        }for row in rows
    }

@tool
def get_topk_rated_product(k: int = 10, keywords: Optional[list[str]] = None):
    """
    Get the top k highest rated products from the catalog.

    Args:
        k(int): Maximum number of products to return.
        keyowrds(Optional[list[str]]): list of search terms.
    Returns:
        list[dict]: List of top k products
    """
    avg_rating = func.avg(models.Reviews.rating).label("avg_rating")

    statement = (
        select(
            models.Reviews.product_id,
            models.Products.name,
            avg_rating,
        )
        .join(
            models.Products,
            models.Reviews.product_id == models.Products.id,
        )
        .group_by(
            models.Reviews.product_id,
            models.Products.name,
        )
    )

    if keywords:
        conditions = [
            models.Products.name.ilike(f"%{keyword}%")
            | models.Products.category.ilike(f"%{keyword}%")
            for keyword in keywords
        ]
        statement = statement.where(or_(*conditions))

    statement = statement.order_by(avg_rating.desc()).limit(k)

    with SessionLocal() as db:
        rows = db.execute(statement).all()

    return [
        {
            "id": row.product_id,
            "name": row.name,
            "avg_rating": round(float(row.avg_rating), 2),
        }
        for row in rows
    ]