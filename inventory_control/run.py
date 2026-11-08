import os
import sys
import socket
import threading
import time
import webbrowser
import uvicorn

# Garante que a pasta atual esteja no PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def porta_em_uso(porta: int = 8000) -> bool:
    """Verifica se a porta já está ocupada por outra instância."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", porta)) == 0


def encontrar_porta_livre(porta_inicial: int = 8000) -> int:
    """Encontra uma porta TCP livre a partir da porta inicial."""
    porta = porta_inicial
    while porta < porta_inicial + 20:
        if not porta_em_uso(porta):
            return porta
        porta += 1
    return porta_inicial


def abrir_navegador(porta: int):
    """Abre o Swagger UI no navegador padrão automaticamente."""
    time.sleep(1.2)
    url = f"http://127.0.0.1:{porta}/docs"
    print(f"\n🌐 Abrindo documentação interativa no navegador: {url} ...\n")
    webbrowser.open(url)


if __name__ == "__main__":
    porta = 8000

    if porta_em_uso(8000):
        print("=" * 65)
        print("ℹ️  O SERVIDOR JÁ ESTÁ EM EXECUÇÃO NA PORTA 8000!")
        print("=" * 65)
        print("Abrindo o navegador diretamente na sua instância ativa...")
        webbrowser.open("http://127.0.0.1:8000/docs")
        print("Pronto! Para reiniciar o servidor, encerre a outra janela do terminal aberta.")
        sys.exit(0)

    print("=" * 65)
    print(f"🚀 INICIANDO API DE CONTROLE DE ESTOQUE NA PORTA {porta}")
    print("=" * 65)
    print(f"O navegador abrirá automaticamente em: http://127.0.0.1:{porta}/docs")
    print("Para encerrar a aplicação, pressione CTRL + C no terminal.\n")

    threading.Thread(target=abrir_navegador, args=(porta,), daemon=True).start()
    uvicorn.run("src.infrastructure.api.main:app", host="127.0.0.1", port=porta, reload=False)
