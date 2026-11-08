import pytest
from src.application.dtos import (
    CriarProdutoRequest,
    AdicionarEstoqueRequest,
    RemoverEstoqueRequest,
    ReservarEstoqueRequest,
    BloquearEstoqueRequest,
)
from src.application.use_cases.inventory_service import ServicoEstoque
from src.domain.exceptions import (
    BloqueioNaoEncontradoException,
    EstoqueInsuficienteException,
    ProdutoDuplicadoException,
    ProdutoNaoEncontradoException,
    ReservaNaoEncontradaException,
)
from src.infrastructure.api.middleware.exception_handlers import manipulador_excecoes_estoque
from src.infrastructure.api.routers.inventory_router import (
    cadastrar_produto,
    consultar_produto,
    entrada_estoque,
    listar_produtos,
    liberar_bloqueio,
    liberar_reserva,
    saida_estoque,
    bloquear_estoque,
    reservar_estoque,
)
from src.infrastructure.persistence.in_memory_repository import RepositorioEstoqueEmMemoria


@pytest.fixture
def servico():
    repo = RepositorioEstoqueEmMemoria()
    return ServicoEstoque(repo)


def test_cadastrar_e_consultar_produto(servico: ServicoEstoque):
    req = CriarProdutoRequest(produto_id="SKU-TEST-1", nome="Cabo HDMI 2.1", quantidade_inicial=25)
    resp = cadastrar_produto(corpo=req, servico=servico)
    
    assert resp.produto_id == "SKU-TEST-1"
    assert resp.nome == "Cabo HDMI 2.1"
    assert resp.quantidade_total == 25
    assert resp.quantidade_disponivel == 25
    assert resp.quantidade_reservada == 0
    assert resp.quantidade_bloqueada == 0

    # Consultar situação
    get_resp = consultar_produto(produto_id="SKU-TEST-1", servico=servico)
    assert get_resp.quantidade_total == 25
    assert get_resp.quantidade_disponivel == 25


def test_listar_produtos(servico: ServicoEstoque):
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-A", nome="Teclado", quantidade_inicial=10), servico=servico)
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-B", nome="Mouse", quantidade_inicial=20), servico=servico)

    itens = listar_produtos(servico=servico)
    assert len(itens) == 2
    skus = {item.produto_id for item in itens}
    assert skus == {"SKU-A", "SKU-B"}


def test_cadastrar_produto_duplicado_lanca_excecao(servico: ServicoEstoque):
    req = CriarProdutoRequest(produto_id="SKU-DUP", nome="Hub USB-C", quantidade_inicial=10)
    cadastrar_produto(req, servico=servico)

    with pytest.raises(ProdutoDuplicadoException):
        cadastrar_produto(req, servico=servico)


def test_consultar_produto_inexistente_lanca_excecao(servico: ServicoEstoque):
    with pytest.raises(ProdutoNaoEncontradoException):
        consultar_produto("NAO-EXISTE", servico=servico)


def test_entrada_e_saida_estoque(servico: ServicoEstoque):
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-OPS", nome="Mousepad", quantidade_inicial=10), servico=servico)

    # Entrada de estoque (+15)
    add_resp = entrada_estoque("SKU-OPS", AdicionarEstoqueRequest(quantidade=15), servico=servico)
    assert add_resp.quantidade_disponivel == 25
    assert add_resp.quantidade_total == 25

    # Saída de estoque (-8)
    rem_resp = saida_estoque("SKU-OPS", RemoverEstoqueRequest(quantidade=8), servico=servico)
    assert rem_resp.quantidade_disponivel == 17
    assert rem_resp.quantidade_total == 17


def test_saida_estoque_insuficiente_lanca_excecao(servico: ServicoEstoque):
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-LOW", nome="SSD 1TB", quantidade_inicial=5), servico=servico)

    with pytest.raises(EstoqueInsuficienteException):
        saida_estoque("SKU-LOW", RemoverEstoqueRequest(quantidade=10), servico=servico)


def test_fluxo_reservar_e_liberar(servico: ServicoEstoque):
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-RES", nome="Teclado Wireless", quantidade_inicial=30), servico=servico)

    # Reservar 10
    res = reservar_estoque("SKU-RES", ReservarEstoqueRequest(quantidade=10, motivo="Pedido E-Commerce #4321"), servico=servico)
    reserva_id = res.id
    assert reserva_id is not None

    # Verificar situação
    situacao = consultar_produto("SKU-RES", servico=servico)
    assert situacao.quantidade_disponivel == 20
    assert situacao.quantidade_reservada == 10
    assert situacao.quantidade_total == 30
    assert len(situacao.reservas) == 1
    assert situacao.reservas[0].id == reserva_id

    # Liberar reserva
    del_res = liberar_reserva("SKU-RES", reserva_id, servico=servico)
    assert del_res.quantidade_disponivel == 30
    assert del_res.quantidade_reservada == 0
    assert len(del_res.reservas) == 0


def test_fluxo_bloquear_e_liberar(servico: ServicoEstoque):
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-BLK", nome="Fonte 650W", quantidade_inicial=20), servico=servico)

    # Bloquear 7
    res = bloquear_estoque("SKU-BLK", BloquearEstoqueRequest(quantidade=7, motivo="Recall Lote 2026"), servico=servico)
    bloqueio_id = res.id

    # Verificar situação
    situacao = consultar_produto("SKU-BLK", servico=servico)
    assert situacao.quantidade_disponivel == 13
    assert situacao.quantidade_bloqueada == 7
    assert situacao.quantidade_total == 20

    # Liberar bloqueio
    del_res = liberar_bloqueio("SKU-BLK", bloqueio_id, servico=servico)
    assert del_res.quantidade_disponivel == 20
    assert del_res.quantidade_bloqueada == 0


def test_liberar_reserva_ou_bloqueio_inexistente(servico: ServicoEstoque):
    cadastrar_produto(CriarProdutoRequest(produto_id="SKU-ITEM", nome="Item", quantidade_inicial=10), servico=servico)

    with pytest.raises(ReservaNaoEncontradaException):
        liberar_reserva("SKU-ITEM", "id-inexistente", servico=servico)

    with pytest.raises(BloqueioNaoEncontradoException):
        liberar_bloqueio("SKU-ITEM", "id-inexistente", servico=servico)


def test_codigos_status_manipulador_excecoes():
    """Valida mapeamento correto de status HTTP e mensagens em português."""
    # 404 ProdutoNaoEncontrado
    r404 = manipulador_excecoes_estoque(None, ProdutoNaoEncontradoException("P1"))
    assert r404.status_code == 404

    # 409 Duplicado
    r409 = manipulador_excecoes_estoque(None, ProdutoDuplicadoException("P1"))
    assert r409.status_code == 409

    # 422 Insuficiente
    r422 = manipulador_excecoes_estoque(None, EstoqueInsuficienteException("P1", 10, 2))
    assert r422.status_code == 422

    # 404 ReservaNaoEncontrada
    r_res404 = manipulador_excecoes_estoque(None, ReservaNaoEncontradaException("R1"))
    assert r_res404.status_code == 404

    # 404 BloqueioNaoEncontrado
    r_blk404 = manipulador_excecoes_estoque(None, BloqueioNaoEncontradoException("B1"))
    assert r_blk404.status_code == 404
