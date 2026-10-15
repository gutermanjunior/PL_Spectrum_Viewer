
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# PL SPECTRUM VIEWER — CONFIGURAÇÃO TIPOGRÁFICA
# =============================================================================
#
# Arquivo:
#     pl_viewer/fonts.py
#
# Projeto:
#     PL Spectrum Viewer
#
# Componente:
#     Gerenciamento de fontes para gráficos científicos.
#
# Data de elaboração:
#     14/10/2026
#
# FINALIDADE
# ----------
# Registrar as fontes tipográficas distribuídas com o projeto e configurar
# sua utilização pelo Matplotlib, independentemente das fontes instaladas
# no sistema operacional.
#
# JUSTIFICATIVA TÉCNICA
# ---------------------
# O Matplotlib utiliza normalmente a família DejaVu Sans, cuja distribuição
# padrão não possui uma variante Semibold de peso 600.
#
# Para preservar a diferenciação tipográfica entre Regular (400),
# Semibold (600) e Bold (700), foi selecionada a família Source Sans 3,
# desenvolvida pela Adobe.
#
# Os arquivos TTF são mantidos no repositório para reduzir a dependência
# das configurações tipográficas locais.
#
# COMPATIBILIDADE
# ---------------
# - Windows
# - macOS
# - Linux (com os requisitos Python e gráficos atendidos)
#
# DEPENDÊNCIAS
# ------------
# - Python 3.12 ou versão compatível com o projeto
# - Matplotlib
# - Arquivos TTF em assets/fonts/
#
# HISTÓRICO DE DESENVOLVIMENTO
# ---------------------------
# 14/10/2026
#   - Proposta de centralização da configuração tipográfica.
#   - Adoção da família Source Sans 3.
#   - Inclusão dos pesos Regular, Semibold e Bold.
#   - Preparação para execução multiplataforma via GitHub.
#
# OBSERVAÇÕES
# -----------
# - As fontes são registradas durante a inicialização da aplicação.
# - O registro não instala fontes no sistema operacional.
# - A configuração deve ocorrer antes da criação dos gráficos.
# - Este módulo configura somente a tipografia do Matplotlib.
# - A tipografia da interface PySide6 é gerenciada separadamente.
#
# LICENÇA DAS FONTES
# ------------------
# Source Sans 3 — Adobe
# SIL Open Font License 1.1
# Consulte assets/fonts/LICENSE.md.
#
# =============================================================================

from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager


def configure_matplotlib_fonts():
    """Registra e configura as fontes utilizadas nos gráficos científicos."""

    # Diretório raiz do projeto.
    project_root = Path(__file__).resolve().parent.parent

    # Diretório das fontes distribuídas com o aplicativo.
    fonts_dir = project_root / "assets" / "fonts"

    # Variantes tipográficas necessárias.
    font_files = (
        "SourceSans3-Regular.ttf",
        "SourceSans3-Semibold.ttf",
        "SourceSans3-Bold.ttf",
    )

    # Registra as fontes diretamente no gerenciador do Matplotlib.
    for filename in font_files:
        font_path = fonts_dir / filename

        if not font_path.is_file():
            raise FileNotFoundError(
                f"Arquivo de fonte não encontrado: {font_path}"
            )

        font_manager.fontManager.addfont(str(font_path))

    # Define a família tipográfica padrão dos gráficos.
    mpl.rcParams["font.family"] = "Source Sans 3"


# =============================================================================
# FIM — CONFIGURAÇÃO TIPOGRÁFICA DO MATPLOTLIB
# =============================================================================
