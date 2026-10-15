# 🔬 PL Spectrum Viewer

**Aplicativo Python para inspeção, comparação, anotação e exportação de espectros de fotoluminescência (PL).**

**Versão documentada:** 1.5 (14 de outubro de 2026)  
**Estado:** aplicação de pesquisa em desenvolvimento; validação automatizada do núcleo científico, com validação interativa da GUI ainda pendente  
**Plataforma de uso:** Windows, com interface PySide6; módulos de processamento e testes executáveis sem interface gráfica

> **Escopo científico.** Este programa visualiza e organiza sinais registrados por um sistema de PL. Não executa uma calibração radiométrica, não determina eficiência quântica, não ajusta automaticamente picos e não caracteriza, isoladamente, um detector QBMD completo. Resultados interpretativos devem ser documentados separadamente dos dados brutos.

## Índice

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Requisitos e instalação](#requisitos-e-instalação)
- [Primeiros passos](#primeiros-passos)
- [Organização das aquisições e metadados](#organização-das-aquisições-e-metadados)
- [Unidades, transformações e interpretação](#unidades-transformações-e-interpretação)
- [Composição de gráficos e formatação](#composição-de-gráficos-e-formatação)
- [Anotações, sessões e exportação](#anotações-sessões-e-exportação)
- [Estrutura do código](#estrutura-do-código)
- [Testes e reprodutibilidade](#testes-e-reprodutibilidade)
- [Limitações conhecidas](#limitações-conhecidas)
- [Histórico de versões](#histórico-de-versões)
- [Dados, autoria e licença](#dados-autoria-e-licença)

## Visão geral

O **PL Spectrum Viewer** foi desenvolvido para comparar aquisições de fotoluminescência, especialmente espectros medidos em campanhas com múltiplas amostras e configurações instrumentais. A interface permite localizar arquivos em uma pasta ou ZIP, selecionar curvas, montar figuras científicas com um ou vários painéis e exportar gráficos vetoriais para relatórios, apresentações e publicações.

A **versão 1.5** introduz composições `1 × 1`, `1 × 2`, `2 × 1` e `2 × 2`, mantendo a correção de **pré-visualização responsiva** introduzida na v1.4.1: o canvas acompanha o espaço disponível na janela, enquanto o tamanho em polegadas é reservado à figura exportada.

### Tecnologias

| Componente | Tecnologia | Papel |
|---|---|---|
| Linguagem | Python | Aplicativo, leitores e análises |
| Interface | PySide6 / Qt | Janela, tabelas e editores |
| Visualização | Matplotlib | Curvas, anotações e composição vetorial |
| Dados numéricos | NumPy | Armazenamento e operações em séries |
| Testes | pytest | Verificações automatizadas |
| Verificação vetorial nos testes | PyMuPDF | Inspeção de exportações PDF |

As versões aceitas das dependências estão em [`requirements.txt`](requirements.txt) e [`requirements-dev.txt`](requirements-dev.txt). Para execução, use uma versão de Python compatível com essas dependências; os testes headless deste pacote foram executados com Python 3.13.

## Funcionalidades

- **Importação de aquisições:** leitura de arquivos binários instrumentais com assinatura DTLG, arquivos `.dat` textuais e fontes em pastas/ZIP; leitores específicos para dados tabulares e validação defensiva.
- **Rastreabilidade:** preservação de metadados instrumentais, detecção de divergências entre cabeçalho e nome do arquivo, comparação de pares binário/`.dat` e registro de avisos.
- **Seleção cronológica:** a ordem das marcações determina a ordem das curvas e as cores da paleta Matplotlib `tab10`, de forma independente em cada painel na composição.
- **Análises não destrutivas:** máximo **discreto** dos pontos adquiridos; fator multiplicativo independente por série (padrão `1`); visualização bruta ou normalizada.
- **Anotações:** linhas verticais (comprimento de onda) e horizontais (sinal), rótulos editáveis, cores, estilos e deslocamentos de texto.
- **Figuras científicas:** títulos, subtítulos, nota inferior, legendas por campos, fontes, espessuras, grade, margens, proporção e espaçamento dos painéis.
- **Textos opcionais:** controles para ocultar/mostrar título, subtítulo e nota inferior **sem perder seu conteúdo**, liberando mais espaço para a área gráfica.
- **Composições:** um a quatro subgráficos (`1×1`, `1×2`, `2×1`, `2×2`), com séries, anotações, títulos, legendas e limites próprios.
- **Persistência:** sessões de edição JSON e compatibilidade com esquemas anteriores, conforme documentação de versão.
- **Saídas:** PDF/SVG vetoriais, PNG e exportações CSV/JSON aplicáveis ao contexto selecionado.

## Requisitos e instalação

### Windows — PowerShell

No diretório local do projeto (por exemplo, `C:\Users\Guterman\GitHub\PL_Spectrum_Viewer`):

```powershell
# Caso ainda não exista um ambiente virtual:
py -3 -m venv .venv

# Ativar o ambiente:
.\.venv\Scripts\Activate.ps1

# Dependências do aplicativo:
python -m pip install -r requirements.txt

# Iniciar:
python main.py
```

Se a política de execução do PowerShell impedir a ativação, **não é necessário alterá-la globalmente**. Execute diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Também existe `iniciar_windows.bat`, que tenta usar `.venv\Scripts\python.exe` quando disponível. **Não há executável `.exe` pré-compilado na distribuição de referência.** O script `criar_exe_windows.bat` fornece uma tentativa de empacotamento local com PyInstaller, sujeita a validação no Windows.

### Abrir uma fonte diretamente

```powershell
python main.py "C:\caminho\para\medicoes"
python main.py "C:\caminho\para\aquisicoes.zip"
```

## Primeiros passos

1. Inicie o aplicativo e escolha **uma pasta** de medições ou **um arquivo ZIP**.
2. Confira a lista de aquisições, incluindo identificação da amostra, condições indicadas e avisos sobre metadados.
3. Marque os espectros que deseja comparar; **a ordem dos cliques determina a ordem das cores**.
4. No painel de formatação, selecione as unidades e ajuste títulos, legendas, limites, linhas e demais parâmetros.
5. Para composições, selecione **Composição — vários painéis**, escolha o layout e atribua curvas ao **painel ativo**.
6. Use **Exportar gráfico…** e selecione explicitamente o filtro `PDF`, `SVG` ou `PNG` na janela de salvamento.
7. Salve também a **sessão de edição JSON**, se precisar reabrir a composição com sua configuração.

> **Dica:** ao renomear uma aquisição, mantenha o mesmo nome-base para o arquivo binário e seu `.dat` correspondente. Atualize a fonte no programa para reprocessar os nomes.

## Organização das aquisições e metadados

O programa reconhece nomes no padrão:

```text
AAAAMMDD HHMM - AMOSTRA [fenda] [temperatura] [fundo_de_escala]
```

Exemplo de **formato**, sem disponibilização do arquivo experimental:

```text
20261009 1524 - 4575 300um 77K 200mV.dat
```

| Campo | Interpretação desse exemplo |
|---|---|
| `20261009 1524` | Data/hora **indicadas no nome**: 09/10/2026 15:24 |
| `4575` | Identificador de amostra |
| `300um` | Abertura nominal de cada uma das duas fendas: 300 µm |
| `77K` | Temperatura indicada: 77 K |
| `200mV` | Fundo de escala configurado para o lock-in: 200 mV |

Também são aceitos identificadores como `4557(1659)` (com código auxiliar) e nomes com ordem variável de fendas, temperatura e fundo de escala. **Campos ausentes não são inventados.**

**Hierarquia de informação:** para identificar a aquisição, os campos presentes no **nome atual do arquivo** prevalecem; os metadados internos do DTLG são preservados e confrontados, com avisos de divergência. Isso **não equivale a uma validação independente** das condições reais de medição. Por exemplo, um cabeçalho com `300 K` e um nome com `77 K` exige verificação do caderno e do operador, não uma correção silenciosa.

O decodificador DTLG é uma **interpretação empírica do formato**, não uma especificação oficial do fabricante. Consulte [`pl_viewer/readers.py`](pl_viewer/readers.py) e [`decodificar_dtlg.py`](decodificar_dtlg.py).

## Unidades, transformações e interpretação

| Grandeza | Representação interna | Opções de exibição |
|---|---|---|
| Comprimento de onda | nm | nm ou Å (`1 nm = 10 Å`) |
| Sinal adquirido | V | V ou mV (`1 V = 1000 mV`) |
| Sinal normalizado | Adimensional | Exibição normalizada |
| Fundo de escala do lock-in | Metadado em mV | Campo descritivo, **não é a unidade do sinal adquirido** |

O fator de cada série altera a visualização, **não os dados instrumentais originais**. Os valores máximos são extraídos de **pontos efetivamente amostrados**, sem ajuste contínuo de pico ou interpolação. O modo normalizado utiliza uma transformação própria e deve ser interpretado separadamente de sinais em V/mV. Linhas horizontais em modo bruto têm referência interna em V; em modo normalizado, a referência é adimensional.

⚠️ **Atenção à comparação quantitativa:** diferentes fendas e fundos de escala podem modificar o sinal registrado. O visualizador não corrige automaticamente resposta espectral do instrumento, largura da fenda, resposta do lock-in, fundo, excitação incidente ou geometria da medida. Fatores manuais não representam calibração experimental.

## Composição de gráficos e formatação

Na v1.5, selecione o modo **Composição — vários painéis** e escolha:

| Layout | Uso típico |
|---|---|
| `1 × 1` | Uma comparação em destaque |
| `1 × 2` | Dois gráficos lado a lado |
| `2 × 1` | Dois gráficos empilhados |
| `2 × 2` | Quatro comparações em uma figura |

Cada painel mantém suas próprias séries (com ordem de cores), título/subtítulo, escalas, anotações e legenda. A seleção dos campos da legenda pode incluir amostra, fendas, T indicada, fundo de escala, data/hora, fator visual e nome do arquivo. Há opções para compartilhar os eixos X e/ou Y **quando as unidades e limites forem compatíveis**.

A **nota inferior em composições é global**, configurada pelo painel `(a)`; títulos/subtítulos são por painel. O espaçamento entre linhas e colunas da composição é ajustável.

**Pré-visualização × exportação:** o tamanho da figura em polegadas controla a **saída** e não força o canvas interativo a ultrapassar o espaço disponível entre os painéis laterais. Esta é a correção histórica **v1.4.1**, mantida na v1.5. Consulte [`ALTERACOES_v1.4.1.md`](ALTERACOES_v1.4.1.md).

## Anotações, sessões e exportação

As anotações admitem referências **verticais** em comprimento de onda e **horizontais** em sinal, com rótulos editáveis e deslocamentos visuais em pontos tipográficos. Essas configurações são guardadas no JSON sem alterar arquivos de aquisição.

O arquivo JSON da sessão v1.5 inclui o estado dos múltiplos painéis (`multipanel_v15`), seus conjuntos ordenados de curvas, opções de texto e formatação. Painéis temporariamente ocultos ao trocar de layout permanecem configurados. Sessões antigas podem ser abertas respeitando as regras de compatibilidade descritas em [`ALTERACOES_v1.5.md`](ALTERACOES_v1.5.md).

**Formatos de exportação:**

- **PDF e SVG:** gráficos vetoriais adequados a edição e inclusão em documentos científicos;
- **PNG:** imagem matricial para apresentações e prévias;
- **CSV bruto:** valores originais; **CSV ajustado:** dados e fatores indicados de maneira explícita;
- **JSON:** sessão de edição e/ou metadados, conforme comando selecionado.

Se o arquivo for salvo sempre como PDF, verifique o **tipo selecionado no diálogo de salvamento**. Alterar apenas a extensão do nome não garante conversão de formato.

## Estrutura do código

```text
PL_Spectrum_Viewer/
├── main.py                     # Ponto de entrada da GUI
├── pl_viewer/
│   ├── gui.py                   # Interface Qt e interação
│   ├── readers.py               # Leitura, metadados e validação de dados
│   ├── models.py                # Modelos de aquisição
│   ├── plotting.py              # Formatação, anotações e sessões
│   ├── multipanel.py            # Composição de múltiplos gráficos
│   ├── selection_order.py       # Ordem de seleção e cores
│   └── exporting.py             # Exportações de dados
├── tests/                       # Testes automatizados
├── requirements.txt
├── requirements-dev.txt
├── iniciar_windows.bat
├── criar_exe_windows.bat
├── decodificar_dtlg.py
├── gerar_exemplo_v15.py
├── ALTERACOES_v*.md             # Registros originais de alterações
├── BUILD_INFO_v*.txt            # Proveniência histórica da construção
├── CHANGELOG.md                 # Histórico consolidado do repositório
└── README.md
```

O diretório `exemplos/` presente no pacote original contém **dados de medições reais e figuras derivadas**. Recomenda-se revisão de autorização/proveniência antes de incluí-lo em repositório remoto. A pasta `assets/`, se adicionada localmente, também deve ser inspecionada.

## Testes e reprodutibilidade

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
```

**Resultado efetivamente observado nesta revisão do pacote v1.5:** `78 passed` em execução headless com Python 3.13.5, NumPy, Matplotlib, pytest e PyMuPDF. **A GUI PySide6 não foi aberta interativamente** neste ambiente; recomenda-se testar no Windows redimensionamento/maximização, troca de painel, anotações por mouse e diálogos de exportação.

**Dependência de dados de referência:** parte dos testes existentes importa o ZIP experimental `exemplos/20261009 PL 4573-4574-4575-4576-4577.zip`. Sem esse arquivo, **a suíte completa não é independente nem reproduzível** no clone. Caso os dados não possam ser distribuídos, o próximo passo de engenharia recomendado é criar fixtures **sintéticas** (sem copiar aquisições reais) e separar testes públicos dos testes de integração com medições privadas. Não declare CI verde em clones sem essa adaptação.

O arquivo [`VALIDACAO_DADOS.txt`](VALIDACAO_DADOS.txt) registra uma análise histórica das aquisições utilizadas na criação do software; não constitui validação universal para outras campanhas.

## Limitações conhecidas

- A unidade original do sinal (V) foi **informada pelo operador**; o software não executa rastreabilidade metrológica da escala do instrumento.
- Metadados de arquivos instrumentais podem estar desatualizados. Divergências são mostradas, não resolvidas automaticamente.
- A identificação por nome do arquivo é uma **regra de organização dos dados**, não evidência de temperatura efetiva.
- A estimativa de máximo não é ajuste de pico, energia de emissão, largura a meia altura nem inferência de parâmetros de heteroestrutura.
- O DTLG é decodificado empiricamente; arquivos diferentes podem exigir revisão dos leitores.
- O script de executável Windows existe, mas **nenhum `.exe` pronto foi validado** nesta distribuição.
- A renderização interativa Qt necessita validação manual adicional, embora o processamento e as saídas vetoriais tenham cobertura automatizada.

## Histórico de versões

O histórico de funcionalidades está organizado em [`CHANGELOG.md`](CHANGELOG.md). Os registros detalhados foram **preservados** em [`ALTERACOES_v1.1.md`](ALTERACOES_v1.1.md), [`ALTERACOES_v1.2.md`](ALTERACOES_v1.2.md), [`ALTERACOES_v1.3.md`](ALTERACOES_v1.3.md), [`ALTERACOES_v1.3.1.md`](ALTERACOES_v1.3.1.md), [`ALTERACOES_v1.3.2.md`](ALTERACOES_v1.3.2.md), [`ALTERACOES_v1.4.md`](ALTERACOES_v1.4.md), [`ALTERACOES_v1.4.1.md`](ALTERACOES_v1.4.1.md) e [`ALTERACOES_v1.5.md`](ALTERACOES_v1.5.md).

**Nota sobre Git:** o primeiro commit será uma **importação do estado v1.5**, não uma recriação artificial de commits retroativos. A história do software anterior à adoção do Git é **documental**, não um log Git verificável.

## Dados, autoria e licença

O software foi preparado para apoiar atividades de pesquisa em fotoluminescência. **Código-fonte, figuras, medições experimentais e materiais de terceiros podem ter titulares ou condições de reutilização diferentes.** A presença de um arquivo no pacote de desenvolvimento não autoriza sua divulgação pública.

Até que a titularidade do código e as permissões aplicáveis sejam avaliadas, recomenda-se **repositório privado**, sem atribuir uma licença open source automaticamente. Quando a situação estiver esclarecida, adicione um arquivo `LICENSE` apropriado e explicite créditos/contribuições confirmados. A publicação no GitHub **não implica**, por si só, cessão de direitos ou liberação dos dados experimentais.

---

**Leitura complementar:** [`ALTERACOES_v1.5.md`](ALTERACOES_v1.5.md) (uso da versão atual), [`ALTERACOES_v1.4.1.md`](ALTERACOES_v1.4.1.md) (layout responsivo), [`CHANGELOG.md`](CHANGELOG.md) (histórico consolidado) e [`docs/GIT_FIRST_COMMIT.md`](docs/GIT_FIRST_COMMIT.md) (primeiro commit com GitHub Desktop).
