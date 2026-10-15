# PL Spectrum Viewer — alterações v1.3.2

**Data:** 13/10/2026. **Base:** v1.3.1 (ordem de seleção determina as cores). **Tipo:** evolução incremental, sem modificar dados de aquisição.

## 1. Anotações horizontais (Y)

Na aba **Gráfico / anotações**, escolha o tipo de linha **Vertical — referência em λ** ou **Horizontal — referência em sinal Y**.

Para uma linha **horizontal**:

1. Escolha **Horizontal — referência em sinal Y**.
2. Digite o valor de **Sinal exibido (Y)** (por exemplo, `0.045`; a vírgula decimal também é aceita).
3. Defina descrição, cor, estilo e a opção **Mostrar valor Y junto do texto**.
4. Defina **Posição X do rótulo** (`6%` a `96%` da largura da área de gráfico) e **Rótulo: ↓ / ↑** (`−240 pt` a `+240 pt`; valor negativo abaixa o texto e positivo sobe o texto, sem mover a linha).
5. Clique em **+ Adicionar**. A tabela distingue `V · ...` e `H · Y=...`.

**Clique ou arrasto:** marque **Adicionar linha ao clicar no gráfico** para inserir uma anotação da orientação escolhida no ponto clicado. Para ajustar uma linha existente, desmarque a primeira opção, marque **Arrastar linhas existentes**, aproxime o cursor até ~9 pixels e arraste. Arrastar linha horizontal altera **Y**; arrastar vertical altera **λ**. A navegação do Matplotlib (zoom/pan) tem prioridade.

Editar, excluir, selecionar, salvar JSON e exportar PDF/SVG/PNG funcionam para os dois tipos. As anotações verticais das versões anteriores continuam aceitas. Para anotações horizontais, o valor Y refere-se à **escala que está desenhada**, não à unidade de comprimento de onda: após multiplicar séries por ×f ou usar normalização, o mesmo valor Y representa uma referência à escala exibida naquele momento. Anotações não são calibração e não alteram os valores brutos.

O JSON preserva a sequência mista no campo `annotations` com `orientation`. Também preserva `vertical_annotations` (formato legado) e registra `horizontal_annotations`. Abertura das edições v1.1, v1.2, v1.3 e v1.3.1 é suportada.

## 2. Arquivo prevalece sobre cabeçalho DTLG

A lista **Amostra / Fenda / Lock-in / T indicada / Arquivo** é baseada no **nome atual do arquivo**, não nos campos internos eventualmente desatualizados. Reconhece formatos como:

- `20261008 1505 - ITA 60um 77K 500mV`
- `20261008 1657 - 4557(1659) 290um 77K 500mV`
- `20261008 1819 - 4555(1655) 77K 290um` (sem fundo de escala no nome; exibido `—`)
- `20261009 1435 - 4573 90um 77K 500mV`

A **amostra principal** é `4557` / `4555`, respectivamente. O valor entre parênteses (`1659` / `1655`) fica visível na coluna da amostra como `4557(1659)` e é registrado **como código auxiliar**, sem lhe atribuir significado experimental não confirmado. Ano-mês-dia e hora-minuto registrados no nome são exibidos na ficha de metadados; essa indicação não verifica autonomamente o horário de aquisição. A temperatura `77K` é a **temperatura indicada no nome** e não uma leitura independente de sensor. A fenda única `290um` é aplicada às entradas e saídas segundo a convenção informada pelo operador.

A coluna **T indicada** usa somente o nome do arquivo. Se a temperatura for informada pelo operador por outro controle, ela permanece no registro separado de temperatura efetiva da sessão, sem modificar essa coluna. **Metadados internos originais DTLG continuam guardados**, inclusive temperatura e fendas: quando existem conflitos, aparecem avisos. Se o campo interno `Nome do arquivo` divergir após uma renomeação, isso também é explicitamente sinalizado. A identificação da amostra não é mais substituída silenciosamente por um cabeçalho contraditório. Somente se não houver identificação possível no nome poderá ocorrer fallback da amostra ao cabeçalho, com aviso de origem.

**Para refletir a renomeação externa:** renomeie o arquivo no sistema operacional e clique em **Atualizar** na aplicação, ou reabra a pasta/ZIP. Para aquisições com dois formatos equivalentes (arquivo binário sem extensão + `.dat`), **renomeie ambos com exatamente o mesmo nome-base**. Caso contrário, o aplicativo os mantém como entradas separadas, pois não presume a equivalência sem comparação.

## 3. Integridade, compatibilidade e validação

- Preservados: cores por ordem de seleção, máximo medido, fatores ×f por série, anotações verticais, exportações CSV, PDF, SVG, PNG e sessões JSON.
- Os dados experimentais binários e `.dat` **não são alterados**; a exportação vetorial contém linhas e textos, não imagens rasterizadas.
- Testes realizados: **48 testes automatizados** em ambiente Python 3.13 (sem GUI), cobrindo também o reconhecimento dos formatos de 8 e 9/10, renomeação com nome antigo no cabeçalho, conflitos de amostra, geometria e posição visual das anotações horizontais, compatibilidade JSON, PDF e SVG.
- A janela **PySide6 não pôde ser executada aqui**; as ações de clique/arrasto e o comportamento do aplicativo completo devem ser validados no Windows antes de usar a versão rotineiramente.

Os exemplos reproduzíveis estão em `exemplos/v1_3_2_anotacoes_horizontal_vertical/` e podem ser gerados novamente com `python gerar_exemplo_v132.py`. Valores e textos das linhas nesse exemplo são **ilustrativos**, não identificação física de emissões.
