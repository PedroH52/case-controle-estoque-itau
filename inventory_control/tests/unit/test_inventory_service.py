import pytest
from src.application.use_cases.inventory_service import InventoryService
from src.domain.exceptions import (
    DuplicateProductException,
    InsufficientStockException,
    ProductNotFoundException,
)
from src.infrastructure.persistence.in_memory_repository import InMemoryInventoryRepository


@pytest.fixture
def service():
    repo = InMemoryInventoryRepository()
    return InventoryService(repo)


def test_create_and_get_product(service: InventoryService):
    res = service.create_product("P1", "Teclado", initial_quantity=10)
    assert res["product_id"] == "P1"
    assert res["total"] == 10
    assert res["available"] == 10

    snap = service.get_snapshot("P1")
    assert snap["product_id"] == "P1"
    assert snap["name"] == "Teclado"


def test_create_duplicate_product(service: InventoryService):
    service.create_product("P1", "Mouse", 5)
    with pytest.raises(DuplicateProductException):
        service.create_product("P1", "Outro Mouse", 10)


def test_product_not_found(service: InventoryService):
    with pytest.raises(ProductNotFoundException):
        service.get_snapshot("NON-EXISTENT")


def test_service_stock_operations(service: InventoryService):
    service.create_product("SKU-1", "Monitor", 20)

    # Add stock
    service.add_stock("SKU-1", 10)
    assert service.get_snapshot("SKU-1")["available"] == 30

    # Remove stock
    service.remove_stock("SKU-1", 5)
    assert service.get_snapshot("SKU-1")["available"] == 25

    # Reserve
    res_id = service.reserve("SKU-1", 10, label="Order #1")
    snap = service.get_snapshot("SKU-1")
    assert snap["available"] == 15
    assert snap["reserved"] == 10

    # Release reservation
    service.release_reservation("SKU-1", res_id)
    assert service.get_snapshot("SKU-1")["available"] == 25
    assert service.get_snapshot("SKU-1")["reserved"] == 0

    # Block
    blk_id = service.block("SKU-1", 5, label="QA Hold")
    snap = service.get_snapshot("SKU-1")
    assert snap["available"] == 20
    assert snap["blocked"] == 5

    # Release block
    service.release_block("SKU-1", blk_id)
    assert service.get_snapshot("SKU-1")["available"] == 25
    assert service.get_snapshot("SKU-1")["blocked"] == 0


def test_list_all_products(service: InventoryService):
    service.create_product("A1", "Item A", 10)
    service.create_product("B2", "Item B", 20)
    products = service.list_products()
    assert len(products) == 2
    ids = {p["product_id"] for p in products}
    assert ids == {"A1", "B2"}
