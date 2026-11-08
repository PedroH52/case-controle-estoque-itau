import pytest
from src.domain.entities.inventory_item import InventoryItem
from src.domain.exceptions import (
    BlockNotFoundException,
    InsufficientStockException,
    InvalidQuantityException,
    ReservationNotFoundException,
)


def assert_inventory_invariants(item: InventoryItem):
    """Auxiliary invariant assertion: Total = Available + Reserved + Blocked."""
    assert item.total == item.available + item.reserved + item.blocked
    assert item.available >= 0
    assert item.reserved >= 0
    assert item.blocked >= 0
    assert item.total >= 0


def test_create_inventory_item_success():
    item = InventoryItem(product_id="PROD-001", name="Teclado Mecânico", initial_quantity=50)
    assert item.product_id == "PROD-001"
    assert item.name == "Teclado Mecânico"
    assert item.available == 50
    assert item.reserved == 0
    assert item.blocked == 0
    assert item.total == 50
    assert_inventory_invariants(item)


def test_create_inventory_item_negative_initial_quantity():
    with pytest.raises(InvalidQuantityException):
        InventoryItem(product_id="PROD-001", name="Mouse", initial_quantity=-5)


def test_add_stock_success():
    item = InventoryItem(product_id="PROD-001", name="Monitor", initial_quantity=10)
    item.add_stock(15)
    assert item.available == 25
    assert item.total == 25
    assert_inventory_invariants(item)


@pytest.mark.parametrize("invalid_qty", [0, -1, -50])
def test_add_stock_invalid_quantity(invalid_qty):
    item = InventoryItem(product_id="PROD-001", name="Monitor", initial_quantity=10)
    with pytest.raises(InvalidQuantityException):
        item.add_stock(invalid_qty)
    assert item.available == 10
    assert_inventory_invariants(item)


def test_remove_stock_success():
    item = InventoryItem(product_id="PROD-001", name="Notebook", initial_quantity=20)
    item.remove_stock(12)
    assert item.available == 8
    assert item.total == 8
    assert_inventory_invariants(item)


def test_remove_stock_insufficient():
    item = InventoryItem(product_id="PROD-001", name="Notebook", initial_quantity=10)
    with pytest.raises(InsufficientStockException) as exc_info:
        item.remove_stock(11)
    
    assert exc_info.value.requested == 11
    assert exc_info.value.available == 10
    # State remains untouched
    assert item.available == 10
    assert item.total == 10
    assert_inventory_invariants(item)


@pytest.mark.parametrize("invalid_qty", [0, -1])
def test_remove_stock_invalid_quantity(invalid_qty):
    item = InventoryItem(product_id="PROD-001", name="Notebook", initial_quantity=10)
    with pytest.raises(InvalidQuantityException):
        item.remove_stock(invalid_qty)
    assert item.available == 10
    assert_inventory_invariants(item)


def test_reserve_and_release_success():
    item = InventoryItem(product_id="PROD-001", name="Cadeira Gamer", initial_quantity=30)
    
    # 1. First reservation
    res1_id = item.reserve(10, label="Pedido #1001")
    assert isinstance(res1_id, str) and len(res1_id) > 0
    assert item.available == 20
    assert item.reserved == 10
    assert item.blocked == 0
    assert item.total == 30
    assert_inventory_invariants(item)

    # 2. Second reservation
    res2_id = item.reserve(5, label="Pedido #1002")
    assert item.available == 15
    assert item.reserved == 15
    assert item.total == 30
    assert_inventory_invariants(item)

    # 3. Release first reservation
    item.release_reservation(res1_id)
    assert item.available == 25
    assert item.reserved == 5
    assert item.total == 30
    assert_inventory_invariants(item)

    # 4. Release second reservation
    item.release_reservation(res2_id)
    assert item.available == 30
    assert item.reserved == 0
    assert item.total == 30
    assert_inventory_invariants(item)


def test_reserve_insufficient_stock():
    item = InventoryItem(product_id="PROD-001", name="Headset", initial_quantity=5)
    with pytest.raises(InsufficientStockException):
        item.reserve(6, label="Pedido #999")
    
    assert item.available == 5
    assert item.reserved == 0
    assert item.total == 5
    assert_inventory_invariants(item)


def test_release_nonexistent_reservation():
    item = InventoryItem(product_id="PROD-001", name="Headset", initial_quantity=5)
    with pytest.raises(ReservationNotFoundException):
        item.release_reservation("non-existent-id")


def test_block_and_release_success():
    item = InventoryItem(product_id="PROD-001", name="Smartphone", initial_quantity=40)

    # 1. Block for quality assurance
    blk1_id = item.block(15, label="Inspeção de Lote")
    assert isinstance(blk1_id, str) and len(blk1_id) > 0
    assert item.available == 25
    assert item.reserved == 0
    assert item.blocked == 15
    assert item.total == 40
    assert_inventory_invariants(item)

    # 2. Block for damaged packaging
    blk2_id = item.block(5, label="Avaria de Transporte")
    assert item.available == 20
    assert item.blocked == 20
    assert item.total == 40
    assert_inventory_invariants(item)

    # 3. Release QA block
    item.release_block(blk1_id)
    assert item.available == 35
    assert item.blocked == 5
    assert item.total == 40
    assert_inventory_invariants(item)

    # 4. Release damage block
    item.release_block(blk2_id)
    assert item.available == 40
    assert item.blocked == 0
    assert item.total == 40
    assert_inventory_invariants(item)


def test_block_insufficient_stock():
    item = InventoryItem(product_id="PROD-001", name="Tablet", initial_quantity=10)
    with pytest.raises(InsufficientStockException):
        item.block(15, label="Manutenção")
    
    assert item.available == 10
    assert item.blocked == 0
    assert item.total == 10
    assert_inventory_invariants(item)


def test_release_nonexistent_block():
    item = InventoryItem(product_id="PROD-001", name="Tablet", initial_quantity=10)
    with pytest.raises(BlockNotFoundException):
        item.release_block("unknown-block-id")


def test_complex_lifecycle_and_invariants():
    """
    Complex end-to-end domain lifecycle testing combinations of
    Entrada, Saída, Reservar, Bloquear, Liberar and Invariants.
    """
    item = InventoryItem(product_id="PROD-ABC", name="Item Multiestados", initial_quantity=100)
    assert_inventory_invariants(item)

    # Reserve 20
    r1 = item.reserve(20, label="R1")
    # Block 30
    b1 = item.block(30, label="B1")
    # Available should be 50
    assert item.available == 50
    assert item.reserved == 20
    assert item.blocked == 30
    assert item.total == 100
    assert_inventory_invariants(item)

    # Outgoing 20
    item.remove_stock(20)
    assert item.available == 30
    assert item.reserved == 20
    assert item.blocked == 30
    assert item.total == 80
    assert_inventory_invariants(item)

    # Incoming 40
    item.add_stock(40)
    assert item.available == 70
    assert item.total == 120
    assert_inventory_invariants(item)

    # Try removing more than available (75 > 70) -> Fail
    with pytest.raises(InsufficientStockException):
        item.remove_stock(75)
    
    # State intact
    assert item.available == 70
    assert item.total == 120
    assert_inventory_invariants(item)

    # Release reservation and block
    item.release_reservation(r1)
    item.release_block(b1)
    assert item.reserved == 0
    assert item.blocked == 0
    assert item.available == 120
    assert item.total == 120
    assert_inventory_invariants(item)


def test_snapshot_representation():
    item = InventoryItem(product_id="PROD-999", name="Webcam 4K", initial_quantity=15)
    res_id = item.reserve(5, label="Order 123")
    blk_id = item.block(2, label="Defective check")

    snap = item.snapshot()
    assert snap["product_id"] == "PROD-999"
    assert snap["name"] == "Webcam 4K"
    assert snap["total"] == 15
    assert snap["available"] == 8
    assert snap["reserved"] == 5
    assert snap["blocked"] == 2
    assert len(snap["reservations"]) == 1
    assert snap["reservations"][0]["id"] == res_id
    assert snap["reservations"][0]["label"] == "Order 123"
    assert len(snap["blocks"]) == 1
    assert snap["blocks"][0]["id"] == blk_id
