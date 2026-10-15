# PL Spectrum Viewer v1.4.1 — Correção do ajuste do gráfico ao painel

**Data:** 13/10/2026. **Base preservada:** `PL_Spectrum_Viewer_v1_4_Formatacao_Unidades_Legendas.zip`.
**Natureza da mudança:** correção de layout e separação da pré-visualização e da exportação, sem alteração dos sinais experimentais ou do processamento físico.

## Defeito informado

Na v1.4, o gráfico no painel central podia ocupar uma dimensão em pixels incompatível com a largura ou altura efetiva entre os painéis esquerdo e direito, cortando a visualização. O quadro tendia a recuperar as dimensões corretas depois de mover a divisória do painel.

## Causa identificada por inspeção do código

Em `pl_viewer/plotting.py`, a função `render_plot` definia incondicionalmente `figure.set_size_inches(settings.figure_width_in, settings.figure_height_in, forward=False)` em **todo** redesenho, inclusive naquele realizado no canvas PySide6. O valor inicial da v1.4 era 13,5 × 7,7 in (1350 × 770 pixels a 100 dpi), que não necessariamente correspondia à área central realmente atribuída pelo `QSplitter`. O `FigureCanvasQTAgg` também calculava um `sizeHint` a partir do tamanho físico da figura, reforçando a disputa de geometria no layout.

**Grau de certeza:** causa de código demonstrada por inspeção; a reprodução visual exata no Windows depende de teste com PySide6 no computador de destino.

## Correções implementadas

1. O `render_plot` ganhou o argumento opcional `resize_figure`. O padrão `True` mantém o comportamento dos scripts antigos que criam figuras independentes. A GUI usa `resize_figure=False`, permitindo que **Qt seja o único responsável pelas dimensões do canvas na tela**.
2. O canvas passou a usar `ResponsiveFigureCanvas`, que oferece ao layout um tamanho inicial compacto, um tamanho mínimo controlado e uma política de expansão. As proporções e o tamanho real do painel central agora determinam a pré-visualização.
3. A exportação constrói uma **figura separada** por `create_export_figure`, usando exatamente largura e altura definidas no editor (em polegadas). O arquivo PDF/SVG/PNG deixa de compartilhar e alterar o objeto de figura da tela.
4. Os quatro botões de exportação foram distribuídos em **duas linhas**, para diminuir a largura mínima exigida pelo painel central.
5. O `QSplitter` dá prioridade de expansão ao painel central e mantém divisórias redimensionáveis. As opções de largura/altura do editor foram explicitadas como **largura/altura exportadas**, com uma nota sobre o ajuste automático da pré-visualização.
6. Os dados originais, seleção e ordem das curvas, cores, limites, fontes, margens, anotações, máximos, fatores, unidades e arquivos de sessão JSON continuam com o mesmo esquema da v1.4.

## Como verificar no Windows

1. Abra o programa e carregue uma pasta ou o ZIP de dados de exemplo.
2. Marque três curvas e confirme que o gráfico permanece **inteiro no painel central**, sem ficar sob as ferramentas laterais.
3. Arraste lentamente cada uma das duas divisórias horizontais do `QSplitter` nos dois sentidos. O desenho deve acompanhar imediatamente a área disponível, sem largura/altura fixas forçadas por `figure_width_in` ou `figure_height_in`.
4. Redimensione/maximize e restaure a janela; repita os testes com uma tela menor e, se possível, escala do Windows de 125%/150%.
5. Em **Gráfico / anotações**, altere as dimensões exportadas para, por exemplo, **18 × 5 in** e pressione **Aplicar formatação**. A pré-visualização deve continuar ocupando somente o painel central, mas o PDF final deve medir **18 × 5 in**.
6. Faça nova exportação e confira anotações verticais/horizontais, legendas, fatores de escala e unidades nm/Å e V/mV.
7. Salve/abra um JSON de edição v1.4 e confirme que ordem das curvas, seleção e formatação permanecem equivalentes.

## Verificações automatizadas

**68 testes automatizados aprovados**, sendo 62 herdados da v1.4 e 6 testes novos (`tests/test_v141.py`). Os testes novos verificam: manutenção das dimensões da pré-visualização após sucessivos redimensionamentos simulados, figura de exportação independente com dimensões PDF corretas, curvas/anotações vetoriais, API pré-existente e ligação estrutural da GUI à nova função.

**Limite da validação:** o pacote PySide6 não está instalado no ambiente de construção e sua instalação falhou por ausência de acesso de rede. Assim, testes de integração visuais da interface em Windows **não foram executados**; a correção é sustentada pela inspeção do código e pelos testes de geometria/Matplotlib independentes de Qt. Nenhum executável `.exe` foi construído.

## Instalação

Mesma instalação da v1.4 (ver `README.md`). Extraia esta versão em **uma pasta nova**, crie o ambiente virtual e instale `requirements.txt`. Não mescle os arquivos com a v1.4 antiga.
