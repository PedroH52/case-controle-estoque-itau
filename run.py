import os
import sys
import socket
import threading
import time
import webbrowser
import uvicorn

root_dir = os.path.dirname(os.path.abspath(__file__))
inventory_dir = os.path.join(root_dir, "inventory_control")

if os.path.exists(inventory_dir):
    os.chdir(inventory_dir)
    sys.path.insert(0, inventory_dir)
else:
    sys.path.insert(0, root_dir)


def porta_em_uso(porta: int = 8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", porta)) == 0


def abrir_navegador(porta: int):
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
