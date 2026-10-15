# PL Spectrum Viewer v1.1 — registro de alterações

**Data:** 13/10/2026. **Base:** `PL_Spectrum_Viewer_v1_MVP.zip` original, não substituído.

## Implementado

- Mantido o código de leitura de DTLG/DAT/CSV/ZIP, deduplicação e metadados originais.
- Novo `pl_viewer/plotting.py`: módulo independente de Qt para formatação científica e exportação PDF/SVG vetorial.
- Opções de título, subtítulo, eixos, nota inferior, limites e unidades nm/Å.
- Linhas verticais com rótulo opcional, comprimento de onda, cor, estilo e altura do texto.
- Editor pela aba direita; inserir por clique, editar por valor/tabela, arrastar linha selecionada, excluir.
- Persistência de anotações e preferências de formatação em JSON independente dos dados brutos.
- Figuras de exemplo e script reprodutível, gerados a partir das aquisições de 09/10/2026.
- Testes automáticos adicionais para leitura, normalização não destrutiva, conversões nm/Å, JSON, PDF/SVG realmente vetoriais.

## Verificações

- 20 testes automatizados aprovados no ambiente Linux de trabalho (15 originais + 5 novos).
- Exportação PDF inspecionada por PyMuPDF: sem imagens incorporadas e com caminhos vetoriais, textos pesquisáveis e linhas.
- Exportação SVG inspecionada como XML: elementos `<text>`, sem `<image>`.
- Interface Qt **não validada interativamente** nesta entrega: `PySide6` indisponível no ambiente e instalação impedida por DNS/rede.
- Empacotamento executável `.exe` **não realizado**.

## Limitações científicas

- O software não corrige resposta espectral, baseline nem calibra o lock-in.
- Rotular uma feição como GaAs, impureza, aceitador ou poço é uma hipótese do usuário, não interpretação automática.
- Não comparar alturas como rendimento ou eficiência quântica, especialmente sob fendas/fundos de escala diferentes.
- O JSON de edição não carrega medidas experimentais nem restaura a temperatura manual; a fonte deve ser reaberta.
