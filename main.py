
#!/usr/bin/env python3
"""Inicializador do PL Spectrum Viewer.

Uso: python main.py [caminho_para_pasta_ou_zip]
"""
import argparse
import sys


def main():
    ap = argparse.ArgumentParser(description="Visualizador de espectros de fotoluminescência")
    ap.add_argument("origem", nargs="?", help="Pasta de medições ou arquivo ZIP")
    args = ap.parse_args()

    # =========================================================================
    # INICIALIZAÇÃO DA CONFIGURAÇÃO TIPOGRÁFICA
    # =========================================================================
    #
    # Data de introdução proposta: 14/10/2026
    # Módulo responsável: pl_viewer/fonts.py
    #
    # Registra as fontes Source Sans 3 distribuídas com o projeto.
    #
    # Objetivos:
    #   - Padronizar a tipografia dos gráficos científicos.
    #   - Preservar os pesos Regular, Semibold e Bold.
    #   - Reduzir diferenças entre Windows e macOS.
    #   - Evitar a necessidade de instalar fontes manualmente.
    #
    # A configuração deve preceder a criação dos gráficos.
    #
    # =========================================================================

    try:
        from pl_viewer.fonts import configure_matplotlib_fonts
        configure_matplotlib_fonts()

    except FileNotFoundError as exc:
        print(
            f"Não foi possível carregar as fontes do projeto:\n{exc}",
            file=sys.stderr
        )
        return 2

    # =========================================================================
    # FIM — INICIALIZAÇÃO DA CONFIGURAÇÃO TIPOGRÁFICA
    # =========================================================================

    try:
        from pl_viewer.gui import run_gui
    except ImportError as exc:
        print("Não foi possível carregar a interface gráfica. Instale as dependências com:\n"
              "  python -m pip install -r requirements.txt\n"
              f"Erro: {exc}", file=sys.stderr)
        return 2

    return run_gui(args.origem)


if __name__ == "__main__":
    sys.exit(main())
