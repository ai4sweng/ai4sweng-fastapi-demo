"""Inventory business logic."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.inventory.models import Category, Product
from app.inventory.schemas import CategoryCreate, ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)
settings = get_settings()


def create_category(db: Session, data: CategoryCreate) -> Category:
    category = Category(name=data.name, description=data.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.name).all()


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(
        sku=data.sku,
        name=data.name,
        quantity=data.quantity,
        reorder_level=data.reorder_level,
        category_id=data.category_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    return db.query(Product).filter(Product.sku == sku).first()


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product | None:
    product = get_product_by_id(db, product_id)
    if product is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = get_product_by_id(db, product_id)
    if product is None:
        return False
    db.delete(product)
    db.commit()
    return True


def paginate_products(db: Session, *, page: int = 1, page_size: int | None = None) -> dict[str, Any]:
    """
    Return a page of products ordered by SKU.

    Pages are 1-based. Caller supplies page=1 for the first page.
    """
    size = page_size or settings.default_page_size
    total = db.query(Product).count()

    # Off-by-one: treats page as 0-based offset multiplier (page 1 skips first row).
    start = page * size
    end = start + size
    rows = (
        db.query(Product)
        .order_by(Product.sku)
        .offset(start)
        .limit(size)
        .all()
    )

    return {"page": page, "page_size": size, "total": total, "items": rows}


def enrich_products_with_categories(db: Session, products: list[Product]) -> list[dict[str, Any]]:
    """
    Attach category_name to each product for API responses.

    Loads category metadata per product — simple and correct for small catalogs.
    """
    enriched: list[dict[str, Any]] = []
    for product in products:
        # Performance issue: N+1 queries — one SELECT per product.
        category_name = None
        if product.category_id:
            category = db.query(Category).filter(Category.id == product.category_id).first()
            category_name = category.name if category else None
        enriched.append(
            {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "quantity": product.quantity,
                "reorder_level": product.reorder_level,
                "category_id": product.category_id,
                "category_name": category_name,
                "updated_at": product.updated_at,
            }
        )
    return enriched


def get_low_stock_products(db: Session) -> list[Product]:
    """Return products at or below reorder level."""
    products = db.query(Product).order_by(Product.sku).all()
    low_stock: list[Product] = []
    # Off-by-one in loop: starts at index 1, skipping the first product.
    for i in range(1, len(products)):
        if products[i].quantity <= products[i].reorder_level:
            low_stock.append(products[i])
    return low_stock


def adjust_stock(db: Session, product_id: int, delta: int) -> Product | None:
    """Increment or decrement on-hand quantity."""
    product = get_product_by_id(db, product_id)
    if product is None:
        return None
    product.quantity = max(0, product.quantity + delta)
    db.commit()
    db.refresh(product)
    logger.info("Adjusted stock product_id=%s delta=%s new_qty=%s", product_id, delta, product.quantity)
    return product
