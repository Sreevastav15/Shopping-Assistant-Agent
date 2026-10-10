from sqlalchemy import select
from database import models
from database.database import SessionLocal
from langchain.tools import tool
from sqlalchemy.dialects.postgresql import UUID
import uuid

def create_cart():
    cart = models.Cart()

    with SessionLocal() as db:
        try:
            db.add(cart)
            db.commit()
            db.refresh(cart)
        except Exception as e:
            print(f"Error creating cart: {e}")
            db.rollback()
            raise

    return str(cart.id)

@tool
def add_items(
    cart_id: str,
    items: list[dict],
) -> dict:
    """Add multiple products to an existing shopping cart.

    Args:
        cart_id: UUID of the existing cart.
        items: List of dictionaries, each containing:
            product_id (int): ID of the product.
            quantity (int): Positive quantity to add.

    Returns:
        A dictionary describing the operation's outcome.
    """
    try:
        cart_uuid = uuid.UUID(cart_id)
    except (ValueError, TypeError, AttributeError):
        return {"success": False, "message": "Invalid cart ID."}

    if not items:
        return {"success": False, "message": "No items provided."}

    # Validate quantities before changing the database.
    try:
        for entry in items:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("product_id"), int)
                or isinstance(entry.get("product_id"), bool)
                or not isinstance(entry.get("quantity", 1), int)
                or isinstance(entry.get("quantity", 1), bool)
                or entry.get("quantity", 1) <= 0
            ):
                return {
                    "success": False,
                    "message": "Each item needs a valid product_id and positive integer quantity.",
                }
    except (TypeError, AttributeError):
        return {"success": False, "message": "Invalid items format."}

    with SessionLocal() as db:
        try:
            cart = db.get(models.Cart, cart_uuid)

            if cart is None:
                return {"success": False, "message": "Cart not found."}

            results = []

            for entry in items:
                product_id = int(entry["product_id"])
                quantity = int(entry.get("quantity", 1))

                price = db.scalar(
                    select(models.Products.price).where(
                        models.Products.id == product_id
                    )
                )

                if price is None:
                    raise ValueError(
                        f"Product ID {product_id} was not found. "
                        "No items were added."
                    )

                price = float(price)

                item = db.scalar(
                    select(models.CartItem).where(
                        models.CartItem.cart_id == cart_uuid,
                        models.CartItem.product_id == product_id,
                    )
                )

                if item is not None:
                    item.quantity += quantity
                    item.net_price = price * item.quantity
                else:
                    item = models.CartItem(
                        cart_id=cart_uuid,
                        product_id=product_id,
                        quantity=quantity,
                        net_price=price * quantity,
                    )
                    db.add(item)

                results.append({
                    "product_id": product_id,
                    "quantity_added": quantity,
                    "quantity_in_cart": (
                        item.quantity if item not in db.new else quantity
                    ),
                    "unit_price": price,
                    "total_price": price * (
                        item.quantity if item not in db.new else quantity
                    ),
                })

            db.commit()

            return {
                "success": True,
                "message": "All items added to cart successfully.",
                "cart_id": str(cart_uuid),
                "items": results,
            }

        except ValueError as e:
            db.rollback()
            return {"success": False, "message": str(e)}

        except Exception:
            db.rollback()
            raise

@tool
def update_item_quantity(
    cart_id: str,
    product_id: int,
    quantity: int,
) -> dict:
    """Set the quantity of an existing product in a cart.

    Args:
        cart_id: UUID of the cart.
        product_id: ID of the product.
        quantity: New positive quantity.
    """
    if isinstance(quantity, bool) or quantity <= 0:
        return {"success": False, "message": "Quantity must be positive."}

    try:
        cart_uuid = uuid.UUID(cart_id)
    except (ValueError, TypeError, AttributeError):
        return {"success": False, "message": "Invalid cart ID."}

    with SessionLocal() as db:
        try:
            item = db.scalar(
                select(models.CartItem).where(
                    models.CartItem.cart_id == cart_uuid,
                    models.CartItem.product_id == product_id,
                )
            )

            if item is None:
                return {
                    "success": False,
                    "message": "Product not found in this cart.",
                }

            price = db.scalar(
                select(models.Products.price).where(
                    models.Products.id == product_id
                )
            )

            item.quantity = quantity
            item.net_price = float(price) * quantity

            db.commit()

            return {
                "success": True,
                "message": "Cart quantity updated.",
                "product_id": product_id,
                "quantity": item.quantity,
                "net_price": item.net_price,
            }

        except Exception:
            db.rollback()
            raise

@tool
def remove_item(cart_id: str, product_id: int) -> dict:
    """Remove a product from a shopping cart.

    Args:
        cart_id: UUID of the cart.
        product_id: ID of the product to remove.
    """
    try:
        cart_uuid = uuid.UUID(cart_id)
    except (ValueError, TypeError, AttributeError):
        return {"success": False, "message": "Invalid cart ID."}

    with SessionLocal() as db:
        try:
            item = db.scalar(
                select(models.CartItem).where(
                    models.CartItem.cart_id == cart_uuid,
                    models.CartItem.product_id == product_id,
                )
            )

            if item is None:
                return {
                    "success": False,
                    "message": "Product not found in this cart.",
                }

            db.delete(item)
            db.commit()

            return {
                "success": True,
                "message": "Product removed from cart.",
                "product_id": product_id,
            }

        except Exception:
            db.rollback()
            raise

@tool
def get_cart_items(cart_id: str) -> dict:
    """Get all items in a shopping cart.

    Args:
        cart_id: UUID of the cart.

    Returns:
        Cart items with product name, unit price, quantity,
        net price, and the total cart value.
    """
    try:
        cart_uuid = uuid.UUID(cart_id)
    except (ValueError, TypeError, AttributeError):
        return {"success": False, "message": "Invalid cart ID."}

    with SessionLocal() as db:
        cart = db.get(models.Cart, cart_uuid)

        if cart is None:
            return {"success": False, "message": "Cart not found."}

        rows = db.execute(
            select(
                models.Products.name,
                models.Products.price,
                models.CartItem.product_id,
                models.CartItem.quantity,
                models.CartItem.net_price,
            )
            .join(
                models.CartItem,
                models.CartItem.product_id == models.Products.id,
            )
            .where(models.CartItem.cart_id == cart_uuid)
            .order_by(models.CartItem.id)
        ).all()

        items = [
            {
                "product_id": row.product_id,
                "product_name": row.name,
                "price": float(row.price),
                "quantity": row.quantity,
                "net_price": float(row.net_price),
            }
            for row in rows
        ]

        return {
            "success": True,
            "cart_id": str(cart_uuid),
            "items": items,
            "total_price": round(sum(item["net_price"] for item in items),2),
        }