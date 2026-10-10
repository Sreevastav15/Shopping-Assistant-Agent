from sqlalchemy import select, func
from database import models
from database.database import SessionLocal
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
