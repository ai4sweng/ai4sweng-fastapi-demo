"""Pydantic schemas for inventory endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None


class CategoryRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    quantity: int = Field(ge=0, default=0)
    reorder_level: int = Field(ge=0, default=5)
    category_id: int | None = None


class ProductRead(BaseModel):
    id: int
    sku: str
    name: str
    quantity: int
    reorder_level: int
    category_id: int | None
    category_name: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    name: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    category_id: int | None = None


class PaginatedProducts(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ProductRead]
