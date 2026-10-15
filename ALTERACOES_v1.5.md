# PL Spectrum Viewer — v1.5 (14/10/2026)

## Origem e continuidade

Base: `PL_Spectrum_Viewer_v1_4_1_Layout_Responsivo.zip`, SHA-256 `69044bc11bf2db73548fc05cfa97a433b9802ef826803b433cba907b2c79d3b6`. Esta versão acrescenta **composições de gráficos** e **três opções de visibilidade de texto**. Não altera o interpretador dos dados instrumentais nem corrige ou calibra medições.

O conserto do layout da v1.4.1 foi preservado: a figura embutida na interface continua com a geometria gerida por Qt (`ResponsiveFigureCanvas`, `QSplitter`, política Expanding). As dimensões em polegadas da aba de formatação são aplicadas **somente à figura de exportação, criada em memória separadamente**. Tanto `render_plot` como `render_composition` recebem `resize_figure=False` durante a pré-visualização.

## Novidade 1 — Composição de painéis

1. Abra uma pasta ou ZIP com espectros, normalmente.
2. Na caixa **Modo**, escolha **Composição — vários painéis**.
3. Na nova faixa acima do gráfico, escolha o layout **1 × 1**, **1 × 2** (lado a lado), **2 × 1** (empilhados) ou **2 × 2**.
4. Escolha **Painel ativo (a), (b), (c) ou (d)**. As caixas na primeira coluna da tabela à esquerda passam a escolher as curvas **somente daquele painel**, na ordem das marcações. Para usar uma aquisição em dois painéis, marque-a em cada um deles.
5. Em **Gráfico / anotações**, ajuste título, unidade, limites, estilos, legenda e anotações do painel atual. Clique **Aplicar formatação ao gráfico** após modificar valores de texto, margens, fontes etc.
6. Mude o **Painel ativo** para editar o seguinte. Também é possível selecionar o painel clicando em sua área gráfica (fora do modo Zoom/Pan).
7. Configure **Compartilhar X**, **Compartilhar Y**, **Espaço H** (vertical, entre linhas) e **Espaço V** (horizontal, entre colunas). Compartilhar eixo exige unidade compatível em todos os painéis visíveis; limites manuais conflitantes são recusados.
8. **Sinal** escolhe entre bruto (V/mV, sem calibração adicional) e normalizado, para todos os painéis na mesma composição.
9. **Salvar como…** gera a figura inteira em um único PDF vetorial, SVG vetorial ou PNG. A posição da legenda e o conjunto de curvas permanecem independentes em cada painel.

As letras (a), (b), (c), (d) fazem parte dos títulos de cada painel quando ele é exibido; não são identificadores físicos das amostras. Curvas usam a paleta por ordem de seleção **em cada painel**. Fatores multiplicativos continuam sendo propriedades de cada aquisição e se aplicam onde quer que ela apareça; o dado bruto não é modificado.

**Nota inferior na composição:** é um texto **global** da figura, configurado no **painel (a)**. Seu campo e sua caixa ficam desabilitados quando outro painel estiver ativo, para evitar ambiguidade. Títulos/subtítulos são independentes de cada painel. Nas composições, os tamanhos da figura exportada e as margens externas também vêm do painel (a).

## Novidade 2 — Texto opcional com recuperação de espaço

Na aba **Gráfico / anotações**, três caixas foram colocadas ao lado dos respectivos campos:

- **Mostrar título**
- **Mostrar subtítulo**
- **Mostrar nota inferior**

Desmarcar **oculta**, mas **não apaga**, o texto. O renderizador reajusta as margens superior/inferior para que os eixos ocupem o espaço disponibilizado. As três opções estão disponíveis tanto no gráfico único quanto na composição. Quando a caixa é marcada novamente, o texto salvo reaparece. Os estados das caixas são persistidos no JSON de edição, e sessões antigas os recebem como `True` por padrão (compatibilidade).

Em uma composição, as opções do título/subtítulo se aplicam ao painel ativo. A nota inferior se aplica à figura inteira, por meio do painel (a).

## Sessões JSON

**Salvar edição…** mantém a estrutura legível pela v1.4.1 e adiciona `multipanel_v15`, com `enabled`, layout, painel ativo, eixos compartilhados, espaçamentos, modo e quatro configurações por painel (seleção ordenada, formatação e anotações). Painéis momentaneamente ocultos pela troca de layout conservam suas configurações. Para editar novamente todos os painéis, abra o JSON na **v1.5**.

**Abrir edição…** aceita JSON antigo v1.1–v1.4.1. Se a fonte de dados diferir, somente estilos/anotações são restaurados; as seleções de aquisições da composição são descartadas. As unidades físicas das anotações são mantidas em nm (verticais) e V (horizontais brutas), com escala normalizada tratada separadamente.

## Reprodutibilidade e limites

- Versão original de sinais: **V**; exibição em V ou mV. O ajuste `500mV` no nome da aquisição é **fundo de escala do lock-in**, não uma conversão do sinal adquirido.
- Comprimento de onda interno: nm; exibição em nm ou Å.
- Metadados instrumentais são conferidos, mas amostra, fendas, temperatura indicada e fundo de escala vêm primeiro do **nome atual do arquivo**.
- Mesmos fatores visuais, ferramenta de máximo discreto, anotações horizontais/verticais, vetores, filtros e exportações CSV das versões anteriores.
- O gráfico de quatro painéis pode exigir figura exportada maior (ex.: 15 × 10 polegadas) e fontes menores para manter a leitura confortável.
- Os espaçamentos configurados são os parâmetros adimensionais do `subplots_adjust` do Matplotlib, não centímetros.
- A **interface PySide6 não foi executada interativamente neste ambiente** por indisponibilidade da dependência. Todos os testes declarados são headless; validar em Windows a troca de painéis, seleção, arrasto, maximização/restauração e exportação pela janela.

## Validação executada

78 testes automatizados aprovados, incluindo 68 testes das versões anteriores, quatro disposições de painéis, persistência/retomada de edições, compartilhamento de eixos, unidades/anotações, preservação dos dados, margens que se expandem sem título/subtítulo/nota e PDF/SVG vetoriais. Exemplo reproduzível: `python gerar_exemplo_v15.py` (usa medições incluídas no ZIP). Seus gráficos estão em `exemplos/v1_5_multiplos_paineis`.
