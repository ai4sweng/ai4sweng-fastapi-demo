"""Inventory HTTP routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.inventory import service
from app.inventory.schemas import (
    CategoryCreate,
    CategoryRead,
    PaginatedProducts,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.users.models import User

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CategoryRead:
    return CategoryRead.model_validate(service.create_category(db, data))


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in service.list_categories(db)]


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProductRead:
    if service.get_product_by_sku(db, data.sku):
        raise HTTPException(status_code=400, detail="SKU already exists")
    product = service.create_product(db, data)
    enriched = service.enrich_products_with_categories(db, [product])[0]
    return ProductRead.model_validate(enriched)


@router.get("/products", response_model=PaginatedProducts)
def list_products(
    page: int = 1,
    page_size: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedProducts:
    result = service.paginate_products(db, page=page, page_size=page_size)
    items = service.enrich_products_with_categories(db, result["items"])
    return PaginatedProducts(
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
        items=[ProductRead.model_validate(item) for item in items],
    )


@router.get("/products/low-stock", response_model=list[ProductRead])
def low_stock_products(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProductRead]:
    products = service.get_low_stock_products(db)
    items = service.enrich_products_with_categories(db, products)
    return [ProductRead.model_validate(item) for item in items]


@router.get("/products/{product_id}", response_model=ProductRead)
def read_product(
    product_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductRead:
    product = service.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    enriched = service.enrich_products_with_categories(db, [product])[0]
    return ProductRead.model_validate(enriched)


@router.patch("/products/{product_id}", response_model=ProductRead)
def patch_product(
    product_id: int,
    data: ProductUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProductRead:
    product = service.update_product(db, product_id, data)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    enriched = service.enrich_products_with_categories(db, [product])[0]
    return ProductRead.model_validate(enriched)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product(
    product_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    if not service.delete_product(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
