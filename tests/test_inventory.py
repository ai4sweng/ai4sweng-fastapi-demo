"""Inventory module tests."""

import pytest


def test_create_and_read_product(client, admin_token, user_token):
    create = client.post(
        "/api/v1/inventory/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "sku": "SKU-100",
            "name": "Monitor",
            "quantity": 12,
            "reorder_level": 4,
            "category_id": 1,
        },
    )
    assert create.status_code == 201
    product_id = create.json()["id"]

    read = client.get(
        f"/api/v1/inventory/products/{product_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert read.status_code == 200
    assert read.json()["sku"] == "SKU-100"
    assert read.json()["category_name"] == "Electronics"


def test_list_products_first_page(client, user_token):
    response = client.get(
        "/api/v1/inventory/products",
        params={"page": 1, "page_size": 2},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    # Off-by-one bug: page 1 uses offset page*size, skipping SKU-001 (and SKU-002).
    assert len(body["items"]) >= 1
    assert all(item["sku"] != "SKU-001" for item in body["items"])


def test_low_stock_endpoint(client, user_token):
    response = client.get(
        "/api/v1/inventory/products/low-stock",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    skus = [item["sku"] for item in response.json()]
    # Off-by-one in get_low_stock_products skips first product (SKU-001 is low stock).
    assert "SKU-001" not in skus
    assert "SKU-003" in skus


def test_create_category(client, admin_token):
    response = client.post(
        "/api/v1/inventory/categories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Office", "description": "Supplies"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Office"


def test_patch_product_quantity(client, admin_token, user_token):
    listing = client.get(
        "/api/v1/inventory/products",
        params={"page": 2, "page_size": 1},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    product_id = listing.json()["items"][0]["id"]
    response = client.patch(
        f"/api/v1/inventory/products/{product_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"quantity": 99},
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 99


# delete_product endpoint has no dedicated unit test (secondary demo gap).
