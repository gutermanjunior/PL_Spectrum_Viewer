# PL Spectrum Viewer — alterações v1.3.1

**Data:** 13/10/2026. **Base preservada:** `PL_Spectrum_Viewer_v1_3_Maximos_e_Fatores.zip`.

## Cores na ordem em que o pesquisador marca os espectros

A ordem de plotagem e as cores agora seguem **a cronologia das marcações na coluna “Exibir (ordem)”**, em lugar da posição fixa dos arquivos, da ordenação por cabeçalho, ou da ordem das linhas da tabela. Isso vale para sobreposição bruta, normalizada e subgráficos separados.

- Se marcar **#4576, depois #4574 e depois #4575**, as curvas aparecem em **azul (#1f77b4), laranja (#ff7f0e) e verde (#2ca02c)**, nessa ordem da legenda e da plotagem.
- A coluna de caixas de seleção exibe **1, 2, 3…** conforme a ordem efetiva; o número tem a cor correspondente e uma dica de ferramenta mostra a posição/código de cor.
- **Desmarcar** uma curva remove sua posição. **Remarcar** a mesma curva a coloca **no final**, recebendo a última cor disponível naquele momento. As demais curvas se renumeram.
- Marcar uma curva que já esteja marcada não altera sua posição.
- **Marcar visíveis** acrescenta somente as ainda não selecionadas, seguindo a **ordem exibida na tabela no momento**; as já marcadas conservam sua posição. **Desmarcar tudo** esvazia a sequência.
- Buscar, filtrar e ordenar a tabela **não alteram** a sequência de seleção. Uma curva marcada e filtrada para fora da tabela **continua no gráfico**, como na v1.3.
- Em uma **nova fonte**, nenhuma curva é marcada automaticamente. Assim, o **primeiro clique do usuário** recebe sempre a primeira cor. Ao recarregar a mesma fonte, a ordem já marcada é preservada, inclusive se a lista estiver vazia.
- A paleta usa as 10 cores `tab10` do Matplotlib e, a partir da curva 11, o ciclo se repete. Portanto, cores podem se repetir para mais de 10 espectros simultâneos; use a legenda para identificá-los.

## Persistência e compatibilidade

**Salvar edição…** grava `selected_spectrum_uids` **na ordem de marcação**, no esquema JSON já existente (`pl-spectrum-viewer-plot-session/v1`). **Abrir edição…** restaura a ordem, desde que a fonte de dados seja a mesma. Sessões anteriores v1.1, v1.2 e v1.3 continuam aceitas; nas antigas, a ordem registrada no campo é usada como ponto de partida, pois o histórico real de cliques anterior não pode ser reconstruído. O arquivo de edição não contém os dados experimentais.

As funções de máximo, fatores ×f individuais, linhas verticais, deslocamento de rótulos e exportação vetorial permanecem. Curvas e valores instrumentais brutos não são modificados.

## Testes

37 testes automatizados passaram em Python 3.13 com Matplotlib/Agg e pytest. Novos testes cobrem seleção cronológica, desmarcar/remarcar, ordem por marcação coletiva, cores em todos os modos, persistência/compatibilidade JSON e não mutação dos sinais experimentais. **A interface gráfica Qt/PySide6 não foi executada neste ambiente** e deve ser conferida no Windows antes do uso científico rotineiro.
