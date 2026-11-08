import concurrent.futures
import threading
from src.domain.entities.inventory_item import InventoryItem
from src.domain.exceptions import InsufficientStockException


def test_concurrent_reservations_race_condition_prevention():
    """
    Test that concurrent reservation requests competing for limited stock
    are strictly serialised by the aggregate lock without race conditions or over-allocation.
    
    Setup:
      - Initial Available: 100
      - 50 concurrent workers each trying to reserve 3 units (50 * 3 = 150 total demand).
      - Available capacity allows at most 33 successful reservations (33 * 3 = 99 units).
      - 17 workers must fail with InsufficientStockException.
    """
    item = InventoryItem(product_id="CONC-001", name="Produto Concorrente", initial_quantity=100)
    
    num_threads = 50
    requested_qty_per_thread = 3
    success_count = 0
    failure_count = 0
    lock = threading.Lock()

    def try_reserve(worker_id: int):
        nonlocal success_count, failure_count
        try:
            item.reserve(requested_qty_per_thread, label=f"Worker-{worker_id}")
            with lock:
                success_count += 1
        except InsufficientStockException:
            with lock:
                failure_count += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_reserve, i) for i in range(num_threads)]
        concurrent.futures.wait(futures)

    # Invariants and business expectations
    assert success_count == 33
    assert failure_count == 17
    assert item.reserved == 33 * 3  # 99
    assert item.available == 1       # 100 - 99 = 1
    assert item.total == 100
    assert item.total == item.available + item.reserved + item.blocked


def test_concurrent_mixed_operations_stress_test():
    """
    Stress test with mixed concurrent operations:
    - Additions
    - Removals
    - Reservations & Releases
    - Blocks & Releases
    """
    item = InventoryItem(product_id="STRESS-001", name="Item Concorrência Mista", initial_quantity=200)

    num_cycles = 100
    
    def worker_reserve_and_release():
        for _ in range(num_cycles):
            try:
                res_id = item.reserve(2, label="Stress-Res")
                # Immediately or shortly release
                item.release_reservation(res_id)
            except InsufficientStockException:
                pass

    def worker_block_and_release():
        for _ in range(num_cycles):
            try:
                blk_id = item.block(2, label="Stress-Blk")
                item.release_block(blk_id)
            except InsufficientStockException:
                pass

    def worker_add_and_remove():
        for _ in range(num_cycles):
            item.add_stock(5)
            try:
                item.remove_stock(5)
            except InsufficientStockException:
                pass

    threads = [
        threading.Thread(target=worker_reserve_and_release),
        threading.Thread(target=worker_reserve_and_release),
        threading.Thread(target=worker_block_and_release),
        threading.Thread(target=worker_block_and_release),
        threading.Thread(target=worker_add_and_remove),
        threading.Thread(target=worker_add_and_remove),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Invariants must hold true
    assert item.total == item.available + item.reserved + item.blocked
    assert item.available >= 0
    assert item.reserved >= 0
    assert item.blocked >= 0
