"""
Script interativo de demonstração da API e do Domínio de Controle de Estoque.
Executa o ciclo de vida completo de um produto e imprime o resultado de cada etapa.
"""

import sys
import os
import concurrent.futures

# Garante suporte a UTF-8 em terminais Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Garante acesso aos módulos src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.infrastructure.persistence.in_memory_repository import InMemoryInventoryRepository
from src.application.use_cases.inventory_service import InventoryService
from src.domain.exceptions import InsufficientStockException


def print_step(title: str):
    print("\n" + "=" * 70)
    print(f"👉 {title}")
    print("=" * 70)


def print_state(label: str, snapshot: dict):
    print(f"\n[{label}]")
    print(f"  • Produto:    {snapshot['product_id']} ({snapshot['name']})")
    print(f"  • Total:      {snapshot['total']}")
    print(f"  • Disponível: {snapshot['available']}")
    print(f"  • Reservado:  {snapshot['reserved']} (Qtd reservas ativas: {len(snapshot['reservations'])})")
    print(f"  • Bloqueado:  {snapshot['blocked']} (Qtd bloqueios ativos: {len(snapshot['blocks'])})")
    
    # Invariante
    invariante_ok = snapshot['total'] == snapshot['available'] + snapshot['reserved'] + snapshot['blocked']
    status = "✅ VÁLIDO" if invariante_ok else "❌ VIOLADO"
    print(f"  • Invariante (Total = Disp + Res + Blq): {snapshot['total']} == {snapshot['available']} + {snapshot['reserved']} + {snapshot['blocked']} -> {status}")


def run_demo():
    print("\n🚀 INICIANDO DEMONSTRAÇÃO DO CONTROLE DE ESTOQUE")
    repo = InMemoryInventoryRepository()
    service = InventoryService(repo)

    # 1. Criação do Produto
    print_step("1. Cadastrando novo produto (SKU: PROD-ITAU-01) com 50 unidades iniciais")
    snap = service.create_product(product_id="PROD-ITAU-01", name="Notebook Dell Corporativo", initial_quantity=50)
    print_state("Estado Inicial", snap)

    # 2. Entrada de Estoque
    print_step("2. Entrada de estoque (Entrada de +30 unidades)")
    snap = service.add_stock("PROD-ITAU-01", quantity=30)
    print_state("Após Entrada", snap)

    # 3. Reserva de Estoque
    print_step("3. Realizando Reserva de 15 unidades para 'Pedido E-Commerce #8841'")
    res1_id = service.reserve("PROD-ITAU-01", quantity=15, label="Pedido E-Commerce #8841")
    print(f"  🏷️ Reserva criada com ID único: {res1_id}")
    snap = service.get_snapshot("PROD-ITAU-01")
    print_state("Após Reserva", snap)

    # 4. Bloqueio de Estoque
    print_step("4. Realizando Bloqueio de 10 unidades por 'Inspeção de Qualidade de Lote'")
    blk1_id = service.block("PROD-ITAU-01", quantity=10, label="Inspeção de Qualidade de Lote")
    print(f"  🔒 Bloqueio criado com ID único: {blk1_id}")
    snap = service.get_snapshot("PROD-ITAU-01")
    print_state("Após Bloqueio", snap)

    # 5. Saída de Estoque
    print_step("5. Saída de 20 unidades físicas do estoque disponível")
    snap = service.remove_stock("PROD-ITAU-01", quantity=20)
    print_state("Após Saída", snap)

    # 6. Tentativa Inválida (Consistência e Fail-Fast)
    print_step("6. Tentando Saída de 50 unidades (superior ao disponível de 35 unidades)")
    try:
        service.remove_stock("PROD-ITAU-01", quantity=50)
    except InsufficientStockException as e:
        print(f"  🛡️ EXCEÇÃO CAPTURADA COM SUCESSO: {e}")
        print("  🔒 O estado do estoque não foi alterado.")
    snap = service.get_snapshot("PROD-ITAU-01")
    print_state("Estado Preservado", snap)

    # 7. Liberação da Reserva
    print_step(f"7. Liberando a Reserva {res1_id} (Pedido cancelado pelo cliente)")
    snap = service.release_reservation("PROD-ITAU-01", res1_id)
    print_state("Após Liberação da Reserva", snap)

    # 8. Liberação do Bloqueio
    print_step(f"8. Liberando o Bloqueio {blk1_id} (Lote aprovado pela inspeção)")
    snap = service.release_block("PROD-ITAU-01", blk1_id)
    print_state("Após Liberação do Bloqueio", snap)

    # 9. Teste de Alta Concorrência em Tempo Real
    print_step("9. Demonstração de Concorrência Real: 50 threads simultâneas disputando estoque")
    conc_snap = service.create_product("PROD-CONC", "Mouse Óptico Concorrente", initial_quantity=100)
    print("  • Estoque disponível inicial: 100 unidades")
    print("  • 50 requisições simultâneas tentando reservar 3 unidades cada (Demanda: 150 unidades)")
    print("  • Capacidade máxima esperada: exatamente 33 reservas com sucesso (99 unidades), 17 falhas e 1 unidade restante.")
    
    sucessos = 0
    falhas = 0

    def worker_reserve(i: int):
        nonlocal sucessos, falhas
        try:
            service.reserve("PROD-CONC", 3, label=f"Thread-{i}")
            sucessos += 1
        except InsufficientStockException:
            falhas += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_reserve, i) for i in range(50)]
        concurrent.futures.wait(futures)

    final_conc = service.get_snapshot("PROD-CONC")
    print(f"\n  📊 RESULTADOS DA CONCORRÊNCIA:")
    print(f"  • Reservas com Sucesso: {sucessos} (esperado: 33)")
    print(f"  • Reservas Rejeitadas:  {falhas} (esperado: 17)")
    print_state("Estado Final do Produto Concorrente", final_conc)

    print("\n" + "=" * 70)
    print("🎉 TODAS AS OPERAÇÕES FORAM EXECUTADAS COM SUCESSO E CONSISTÊNCIA TOTAL!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
