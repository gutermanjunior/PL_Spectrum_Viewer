# PL Spectrum Viewer v1.5 — análise de fotoluminescência

**Novidade v1.5:** agora você pode compor **1 × 1, 1 × 2, 2 × 1 ou 2 × 2 gráficos** na mesma figura, atribuindo curvas, escalas, títulos, legendas e anotações de forma independente. Na aba **Gráfico / anotações**, as caixas **Mostrar título**, **Mostrar subtítulo** e **Mostrar nota inferior** ocultam cada elemento sem apagar o texto, e o gráfico recupera o espaço correspondente. Para composições, a nota inferior é única e editada no painel (a).

**Importante:** foi preservada a correção do *layout responsivo* v1.4.1: a área central é dimensionada pela janela Qt, e largura/altura em polegadas controlam **apenas as figuras exportadas**. A v1.5 também mantém a interpretação do nome do arquivo prioritária, V/mV, nm/Å, fatores de série, máximos, anotações e PDF/SVG vetoriais. Veja `ALTERACOES_v1.5.md` para o tutorial completo.

**Validação:** 78 testes automatizados headless aprovados; teste visual e de arrasto com PySide6 no Windows ainda pendente. Os dados instrumentais não são modificados.

---

# 🔬 PL Spectrum Viewer — formatação científica de espectros (v1.4.1)

## Correção v1.4.1 — pré-visualização responsiva nos três painéis

A v1.4.1 corrige o desenho do gráfico que podia ultrapassar o espaço disponível entre os painéis esquerdo e direito. A **pré-visualização acompanha o tamanho real do painel central**, inclusive quando você move as divisórias; os controles **Largura exportada** e **Altura exportada** (em polegadas) determinam **somente** o tamanho da figura PDF/SVG/PNG. Os dados e recursos científicos da v1.4 não mudaram.

**Validação:** 68 testes automatizados passaram (62 herdados + 6 novos); a GUI PySide6 não foi executada aqui por indisponibilidade da dependência e falta de rede. Consulte `ALTERACOES_v1.4.1.md` para análise da causa, mudanças no código e teste manual recomendado no Windows.

---

## Novidades v1.4 — figura personalizável e unidades confirmadas

A unidade original de sinal informada pelo operador é **V**. Em **Gráfico / anotações**, use **Unidade Y** para alternar entre **V e mV**, mantendo os dados originais em V. A unidade X pode alternar entre nm e Å. O eixo Y aparece como **Sinal do lock-in (V)** ou **Sinal do lock-in (mV)**; o fundo de escala `200mV` presente no nome do arquivo continua sendo um ajuste instrumental distinto.

Agora é possível controlar **largura/altura** (e proporção), **família tipográfica**, tamanhos de todas as fontes (título, eixos, números, legenda, rótulos de anotações e rodapé), espessura/estilo das curvas e das linhas de referência, intensidade da grade, margens, espaçamento dos subgráficos, posição/colunas/moldura da legenda e, sobretudo, **escolher os campos que entram na legenda**: amostra, fendas, T indicada, escala do lock-in, data/hora, fator ×f e nome de arquivo. Os campos ausentes não são inventados.

As linhas horizontais guardam sua referência em V (ou em escala normalizada, quando inseridas no modo correspondente) e são convertidas com a mudança de unidade; linhas verticais continuam com referência interna em nm. Os arquivos de edição antigos continuam compatíveis. PDF/SVG preservam o tamanho/proporção e a composição vetorial; os CSVs brutos permanecem em V, com colunas `*_V` adicionais.

**Validação v1.4:** 62 testes automatizados passaram, incluindo leitura de dados reais, gráficos, anotações, conversão V/mV, legenda, sessão JSON e exportação PDF/SVG. **A interface PySide6 não pôde ser aberta neste ambiente e precisa de validação interativa no Windows.** Consulte `ALTERACOES_v1.4.md` para instruções detalhadas, ressalvas e valores aceitos.

---



## Novidades v1.3.2 — linhas horizontais e identificação por nome do arquivo

O editor de anotações oferece agora **linhas verticais e horizontais**. Para linhas horizontais, indique o **valor Y do sinal exibido**, texto, cor, estilo, **posição X do rótulo (%)** e deslocamento vertical do texto (**↓ / ↑ em pontos tipográficos**). É possível inserir por clique e arrastar tanto linhas verticais quanto horizontais. As duas orientações são gravadas no JSON de edição e aparecem nos PDFs e SVGs vetoriais. **O sinal horizontal corresponde à escala exibida**, inclusive quando há multiplicação ou normalização; não constitui calibração.

**Nomes dos arquivos são a fonte prioritária** para amostra, abertura nominal das duas fendas, fundo de escala do lock-in e temperatura indicada. Ex.: `20261008 1657 - 4557(1659) 290um 77K 500mV` resulta em **amostra 4557 (código auxiliar 1659)**, fendas nominalmente 290 µm, T indicada 77 K e lock-in 500 mV. `4555(1655) 77K 290um` é aceito mesmo sem `mV` (o campo fica ausente). Data/hora também vêm do nome. Cabeçalhos DTLG continuam armazenados e são comparados para alertas, **sem substituir o nome atual**. Após renomear um arquivo no sistema operacional, clique em **Atualizar** (se houver `.dat` e binário para o mesmo espectro, renomeie os dois). Veja `ALTERACOES_v1.3.2.md` para condições, limites e instruções completas.

**Validação v1.3.2:** 48 testes automatizados passaram, incluindo PDF/SVG vetoriais. A GUI PySide6 não foi executada neste ambiente e precisa de validação no Windows. Não há `.exe` pré-compilado nesta entrega.

## Novidades v1.3.1 — ordem de marcação define cores e legenda

A coluna **Exibir (ordem)** agora atribui as cores pela **ordem dos cliques nas caixas**: a primeira curva marcada fica azul, a segunda laranja, a terceira verde, e assim sucessivamente. Exemplo: marcar **#4576 → #4574 → #4575** gera exatamente essa sequência e também essa ordem na legenda. Os números **1, 2, 3…** aparecem junto das caixas.

Ao **desmarcar** e **remarcar** um espectro, ele passa para o final da sequência e recebe uma nova cor. Filtrar ou reordenar a tabela não muda a ordem de plotagem; **Marcar visíveis** acrescenta novas curvas seguindo a ordem visível e respeitando aquelas já marcadas. **Desmarcar tudo** apaga a sequência. Ao abrir um conjunto novo, **nada é marcado automaticamente** para que seu primeiro clique escolha a primeira cor. Recarregar a mesma fonte preserva a seleção. Se houver mais de 10 curvas, a paleta Matplotlib tab10 volta à primeira cor.

A sequência fica salva no mesmo JSON de edição (campo `selected_spectrum_uids`) e é restaurada ao abrir a edição com a mesma fonte. As sessões antigas continuam aceitas, mas seu histórico real de cliques não existe: utiliza-se a ordem registrada no JSON. A paleta também é consistente nos subgráficos separados; valores brutos, máximos, fatores e anotações permanecem intactos.

Um exemplo em PNG/SVG/JSON está em `exemplos/v1_3_1_cores_por_selecao/`, reproduzível com `python gerar_exemplo_v131.py`. Detalhes em `ALTERACOES_v1.3.1.md`.


Aplicativo local para **Windows**, desenvolvido em Python com **PySide6** e **Matplotlib**. A interface permite abrir uma pasta ou arquivo ZIP de espectros, filtrar as aquisições, marcar curvas para visualização, comparar espectros e exportar dados.

> **Estado da entrega (base v1.3 com extensões até v1.4.1, 13/10/2026):** evolução do MVP original, não aplicativo refeito do zero. O leitor DTLG/DAT, a geração de figuras PDF/SVG genuinamente vetoriais, o JSON de edição e a preservação dos dados foram testados automaticamente com as aquisições reais de 9/10/2026. **A interface PySide6 não pôde ser aberta neste ambiente** (biblioteca indisponível e rede sem acesso). É necessário validar cliques, edição, arrasto e exportação pela GUI no Windows. Não há `.exe` neste pacote.

## 1. Instalação no Windows

**Pré-requisito:** Python **3.11 ou 3.12**, instalado com o `pip`, e conexão à internet para instalar as dependências (uma única vez).

Extraia o ZIP do projeto em uma pasta de seu computador. Abra o **Prompt de Comando** ou **PowerShell** nessa pasta e execute:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Se o Windows impedir a criação de ambientes virtuais, verifique sua instalação do Python. Os comandos acima não exigem ativar o ambiente virtual.

Para iniciar diretamente com a pasta de medições:

```powershell
.venv\Scripts\python.exe main.py "C:\caminho\para\medidas"
```

Ou diretamente com um ZIP:

```powershell
.venv\Scripts\python.exe main.py "exemplos\20261009 PL 4573-4574-4575-4576-4577.zip"
```

Também existe `iniciar_windows.bat`; ele utiliza automaticamente `.venv` quando essa pasta existe ou, caso contrário, usa o Python padrão. **Recomenda-se usar `.venv`** para evitar conflito entre instalações.

## Novidade v1.3 — máximo e multiplicação de séries

A v1.3 acrescenta o bloco **Análise da série destacada**, abaixo da lista de aquisições (painel esquerdo). **Clique em uma linha da tabela** para definir a série alvo. A seleção da linha é diferente das caixas da coluna **Exibir**, que controlam quais curvas aparecem no gráfico.

1. **Máximo e comprimento de onda:** clique **Localizar máximo**. Um painel apresenta o maior valor dentre os pontos efetivamente adquiridos da série alvo, com a coordenada correspondente em nm ou Å. Se o máximo for único, ele recebe um marcador e uma etiqueta vetorial na curva. Não se faz ajuste, interpolação ou atribuição física. O botão marca automaticamente a curva para exibição se necessário.
2. **Fator da série:** digite um valor em **Multiplicar sinal por** (padrão 1) e clique em **Aplicar fator**. Apenas a série destacada é multiplicada. Por exemplo, `2.5` faz o gráfico exibir duas vezes e meia seu sinal registrado; `0.5` reduz à metade; `1` não modifica. Use **Restaurar ×1** para retirar um fator. Fatores negativos e zero são aceitos, com ressalvas para a interpretação do máximo; valores são adimensionais e limitados a ±1 000 000. Há oito casas decimais no campo.
3. **Dados intactos:** fatores valem só para visualização, cálculo de máximo multiplicado e exportações explicitamente ajustadas. Os pontos brutos não são alterados e continuam acessíveis. Se houver fator negativo, o máximo após multiplicação pode corresponder ao mínimo bruto. Se houver empates (como fator 0), o programa informa que não existe pico máximo único e não desenha um marcador de pico.
4. **Dois CSVs:** **Exportar CSV bruto…** preserva o comportamento das versões anteriores; **Exportar CSV ajustado…** cria um CSV independente com ambas as colunas de sinal e o fator aplicado. Os gráficos PDF/SVG também incorporam a escala por curva e o marcador de máximo.
5. **Guardar a edição:** **Salvar edição…** passa a registrar fatores por identificador de aquisição e a seleção do destaque de pico. **Abrir edição…** os restaura somente se a fonte de dados corresponder à sessão anterior. Arquivos de edição das versões 1.1/1.2 permanecem compatíveis (fator 1 por padrão).

**Importante:** o máximo é global em toda a aquisição, mesmo que você tenha dado zoom em uma pequena faixa. Se a marcação ficar fora dos limites definidos dos eixos, restaure o enquadramento ou altere os limites X/Y. Os valores apresentados são instrumentais, não calibrados; multiplicar uma curva não permite inferir eficiência quântica. O modo de normalização pelo máximo pode cancelar o efeito de fatores positivos; use **Sobreposição — sinal bruto** para comparar alturas ajustadas.

Exemplo reprodutível em `exemplos/v1_3_maximo_e_fatores/`, que assinala o máximo da #4575 e multiplica apenas a #4576 por 2. O gerador é `gerar_exemplo_v13.py`.

Para notas de implementação e validação, consulte `ALTERACOES_v1.3.md`.

## Recursos de figuras científicas editáveis (v1.1–v1.2)

A aba **Gráfico / anotações** (painel direito) oferece:

1. **Título, subtítulo, nomes dos eixos, nota inferior e limites X/Y.** Digite os valores e clique em **Aplicar formatação**. Deixe limites vazios para o ajuste automático. Títulos como `October 9, 2026 | Low-temperature growth series` reproduzem a estrutura das imagens de referência.
2. **Unidade de comprimento de onda nm ou Å.** O eixo X, as marcações e os limites mudam juntos. A aquisição internamente continua em **nm**; a unidade do eixo não altera nem grava os dados brutos.
3. **Adicionar linha vertical por valor:** preencha o comprimento de onda na unidade mostrada (`824.5` nm ou `8245` Å), escreva a descrição, escolha a cor, estilo, altura e deslocamento horizontal do rótulo, e clique em **+ Adicionar**. Várias linhas podem coexistir, com caixas de texto deslocadas independentemente nos eixos vertical e horizontal (evita sobreposição).
4. **Adicionar linha por clique:** marque **Adicionar linha ao clicar no gráfico** e clique na posição desejada do eixo X. O programa preenche a coordenada e adiciona uma nova linha com os campos atuais. Desmarque para voltar à navegação normal.
5. **Mover uma linha:** marque **Arrastar linhas existentes no gráfico** (desmarque a opção de adicionar), clique até 9 pixels de uma linha, arraste e solte. Se a barra de zoom/pan do Matplotlib estiver ativa, o gesto será reservado à navegação. Também é possível corrigir a posição numericamente: clique na linha da tabela, edite o comprimento de onda e use **Atualizar**.
6. **Editar/retirar:** clique no registro na pequena tabela de linhas, altere descrição, estilo, cor, altura ou deslocamento horizontal e use **Atualizar**; **Excluir** retira a marcação. A altura é a porcentagem da área do gráfico, não um sinal físico em mV. **Na v1.2**, o campo **Rótulo: ← / →** controla exclusivamente o texto em **pontos tipográficos (`pt`)**, sem deslocar a linha: `−45 pt` move o rótulo para a esquerda; `0 pt` mantém centralizado; `+45 pt` move para a direita. As setas do campo alteram o valor de 5 em 5 pt. O deslocamento independe de nm/Å, é mantido no PDF/SVG e persiste no JSON de edição. Confira visualmente a posição após um zoom ou troca de formato, sobretudo se o texto estiver perto da borda do gráfico.
7. **PDF e SVG vetoriais:** clique **Exportar gráfico…** e escolha `PDF vetorial (*.pdf)` ou `SVG vetorial (*.svg)`. Linhas de dados, marcações, rótulos, grade, legenda e eixos são exportados como elementos vetoriais; textos permanecem pesquisáveis e o SVG utiliza objetos `<text>` editáveis. `PNG` continua disponível para apresentações.
8. **Salvar/abrir edição:** clique **Salvar edição…** para um `.json` contendo apenas formatação, anotações, curvas selecionadas por ID e a referência à fonte. Abra novamente os espectros originais e use **Abrir edição…** para continuar. O JSON **não** incorpora as medições; mantenha o ZIP ou pasta de origem. Se a fonte for diferente, somente a aparência e as linhas poderão ser importadas mediante confirmação.

**Exemplos já gerados:** `exemplos/figuras_vetoriais/` contém dois conjuntos reais de 09/10/2026 em PDF, SVG e PNG, com formato semelhante às imagens fornecidas. O exemplo das amostras #4574–#4576 mostra marcações demonstrativas em 824,5 e 834 nm, com rótulos deslocados respectivamente para a esquerda e para a direita; **não atribui causas físicas** a essas feições. O segundo mostra #4573 vs. #4577 sem anotações.

**Rigor instrumental:** os nomes das aquisições indicam fenda e escala do lock-in, mas não comprovam calibração de intensidade. O gráfico nunca interpreta altura de pico como eficiência quântica. Temperatura informada por operador e discrepâncias de cabeçalho continuam documentadas. Modo normalizado é somente visual; o CSV mantém os valores de aquisição. As etiquetas inseridas pelo usuário são interpretações do usuário, não resultados do aplicativo.

### Gerar novamente os exemplos vetoriais

Após instalar o ambiente Python, execute na pasta `PL_Spectrum_Viewer`:

```powershell
.venv\Scripts\python.exe gerar_exemplos_vetoriais.py
```

Os arquivos de saída são novos; nenhum DTLG ou DAT original é modificado.

## 2. Uso

1. Clique em **Abrir pasta…** ou **Abrir ZIP…**.
2. Aguarde a identificação dos arquivos. Espectros equivalentes em DTLG e `.dat` aparecem como **uma aquisição**, com os dois caminhos listados nos metadados.
3. Use a caixa de pesquisa e os filtros por **amostra, abertura indicada no nome e fundo de escala do lock-in**.
4. **Marque as caixas na primeira coluna** para incluir ou remover espectros do gráfico. Para selecionar vários rapidamente, use **Marcar visíveis**.
5. Use a barra padrão do Matplotlib acima do gráfico para **zoom, deslocamento e restauração**; os controles do lado direito exibem todos os metadados.
6. Escolha o modo **Sobreposição — sinal bruto** (padrão), **Curvas separadas** ou **Sobreposição — normalizadas**. Modos separados e normalizados são recursos iniciais; não substituem uma análise quantitativa calibrada.
7. Para registrar a temperatura efetiva informada pelo operador, marque as aquisições, digite uma temperatura em K (ex.: `77`) e clique em **Aplicar às marcadas**. Isso **não altera arquivos originais** nem o valor de 300 K presente no cabeçalho.
8. Use os botões inferiores para exportar o gráfico em PNG/SVG/PDF, os pontos originais em CSV e os metadados em JSON.
9. Quando mudar de pasta, use **Abrir pasta…** novamente. Nenhuma alteração de código é necessária.

**Filtros não desmarcam medidas:** se uma curva foi marcada e depois escondida por um filtro, ela continuará no gráfico. O rodapé da tabela apresenta as contagens de curvas visíveis e marcadas.

**Arquivos DAT sem unidade declarada:** a aplicação usa inicialmente uma **heurística de escala** (por exemplo, valores 7500–9500 são interpretados como Å, com aviso). Se a inferência estiver incorreta, altere a opção **DAT: detectar unidade** para **DAT: Å (forçar)** ou **DAT: nm (forçar)** e a pasta será recarregada. Para pares coincidentes DTLG/DAT, as leituras espectrais são comparadas antes da fusão.

## 3. Formatos reconhecidos

| Formato | Interpretação | Observação |
|---|---|---|
| DTLG (arquivo sem extensão ou binário com assinatura) | Metadados e curva binários | Decodificador empírico, específico da família validada |
| `.dat` | Tabela de duas colunas X, Y | Espaços, TAB, ponto decimal e `;` com vírgula decimal |
| `.csv` e `.txt` | Tabelas numéricas simples | Leitura de duas primeiras colunas; demais geram aviso |
| `.zip` | Fonte com os arquivos acima | Abertura de ZIP sem modificar/extrair no diretório original |

Arquivos não reconhecidos são ignorados; arquivos identificados com estrutura inválida produzem erros individualizados. Um arquivo ruim não impede a exibição de outros.

A equivalência entre DTLG e `.dat` exige **mesmo nome-base**, mesmo eixo e sinais numericamente compatíveis (`rtol=2e-6`, `atol=1e-9`). Caso não coincidam, os dois são preservados e avisados. O programa não inventa a unidade física do sinal registrado.

## 4. Resultados validados no conjunto de 9/10/2026

O arquivo `exemplos/20261009 PL 4573-4574-4575-4576-4577.zip` acompanha a distribuição para validação e demonstração:

- **26 arquivos** examinados: **13 binários** e **13 arquivos `.dat`**.
- **13 aquisições distintas**; todos os 13 pares conferiram numericamente ponto a ponto.
- **7 aquisições com 301 pontos**, **6 com 401 pontos**; passo espectral registrado de **0,5 nm**.
- Amostras presentes: **4573, 4574, 4575, 4576, 4577**. A referência **ITA não está presente nesse ZIP**; um teste automatizado comprova seu reconhecimento em outra pasta.
- Temperatura no cabeçalho binário: **300 K**; nos nomes: **77 K**. O operador informou que a temperatura real das medições iniciais correspondeu à ebulição do nitrogênio líquido (~77 K). O aplicativo preserva as fontes separadamente; a informação do operador deve ser aplicada pela interface para identificação explícita.
- Todos os cabeçalhos binários registram **0,4 mm (400 µm)** para fendas de entrada e saída, embora os nomes indiquem aberturas variadas. O software **não decide automaticamente** qual registro corrigir.
- Os nomes indicam faixas de lock-in em mV, mas os sinais binários e DAT não trazem calibração física verificada. Valores como `500mV` **não são intensidade de emissão**.

Para auditar o ZIP sem abrir a interface:

```powershell
.venv\Scripts\python.exe validar_dados.py "exemplos\20261009 PL 4573-4574-4575-4576-4577.zip"
```

## 5. Testes automatizados

Após instalar as dependências de desenvolvimento:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest tests -q
```

Os testes verificam: 13 pares, comparação numérica ponto a ponto, leitura de ITA em pasta independente, troca de pasta, unidade Å/nm, arquivos inválidos, dados divergentes, fendas e temperatura em conflito, possíveis platôs e exportação CSV/JSON.

## 6. Arquivos do projeto

```text
PL_Spectrum_Viewer/
├── main.py                     # inicializa a interface
├── validar_dados.py            # auditoria sem PySide6
├── decodificar_dtlg.py         # decodificador experimental original
├── requirements.txt
├── requirements-dev.txt
├── iniciar_windows.bat
├── criar_exe_windows.bat
├── pl_viewer/
│   ├── __init__.py
│   ├── models.py                # registro de aquisição e rastreabilidade
│   ├── readers.py               # leitura e validação dos formatos
│   ├── exporting.py             # CSV e JSON
│   └── gui.py                   # interface PySide6 e gráficos
├── tests/
│   └── test_readers.py
└── exemplos/
    └── 20261009 PL 4573-4574-4575-4576-4577.zip
```

## 7. Construção posterior do executável Windows

Na máquina Windows, após conseguir abrir a interface pelo Python:

```powershell
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name PL_Spectrum_Viewer main.py
```

O executável será criado em `dist\PL_Spectrum_Viewer\PL_Spectrum_Viewer.exe`. O `.exe` gerado ainda precisará ser testado com o ZIP real antes da distribuição. Não é possível gerar um executável nativo de Windows de forma confiável a partir do ambiente atual sem as bibliotecas de build compatíveis.

## 8. Limitações científicas e operacionais

- **Sem correção instrumental absoluta:** ITA não é usada automaticamente para correção ou calibração. Não há curva de resposta espectral, potência medida do laser ou conversão auditada da fotocorrente para intensidade física.
- **Sem comparação quantitativa garantida:** curvas com diferentes fendas, lock-in, ganho, alinhamento ou condições ópticas podem apresentar sinais distintos por causa do sistema de aquisição. A interface alerta diferenças de parâmetros disponíveis, sem promover equivalência de condições.
- **Sem calibrar o sinal em mV:** usa **Sinal armazenado (unidade não verificada)**, mantendo a sensibilidade do lock-in como metadado.
- **Fendas e temperatura divergentes:** são exibidas com suas fontes. A edição manual da temperatura vale apenas na sessão; o cabeçalho original é preservado.
- **Inferência de unidade em DAT:** arquivos com formatos inéditos podem exigir escolha manual Å/nm, aperfeiçoamento do parser ou rejeição controlada.
- **DTLG não universal:** offsets e tipos do decodificador original foram validados apenas para esta família de arquivos. Novos formatos podem não ser aceitos.
- **Detecção de saturação preliminar:** platôs exatos consecutivos no máximo são sinalizados; outros casos de saturação podem passar sem aviso.
- **Normalização por máximo:** ferramenta apenas visual, especialmente limitada quando há saturação ou linha de base significativa.
- **Sessões de edição v1.1/v1.2 (parciais):** a formatação, as linhas verticais e a seleção de curvas são persistidas em JSON separado. A temperatura manual registrada na GUI não é restaurada automaticamente; para reproduzir essa informação, consulte o JSON de metadados e reaplique-a. O JSON de edição não inclui dados brutos.
- **Limites de segurança/desempenho:** leitor limita tamanho de arquivo e número de pontos para reduzir risco de leitura excessiva. Gráficos separados usam no máximo 16 espectros simultâneos; sobreposições não impõem esse limite.
- **Interface não validada em execução nesta entrega:** PySide6 e Qt não estavam disponíveis no ambiente de desenvolvimento. Testar abertura, clique, arrasto, alteração de unidades, recuperação de edição e exportações pela GUI no Windows.

## 9. Melhorias previstas (Etapas 2 e 3)

Detecção automática de pico, análise de FWHM, integração de bandas, anotação de energia em eV, curvas de referência ITA sob protocolo de calibração, filtros adicionais e empacotamento final validado. Linhas de referência, edição de texto e sessões de formatação foram implementadas na v1.1; deslocamento horizontal do texto foi acrescentado na v1.2.

Os dados binários e DAT fornecidos são **mantidos intactos**. Exportações e anotações são gravadas somente em arquivos novos escolhidos pelo operador.

### Compatibilidade de edições antigas (v1.1)

Arquivos `.json` salvos na v1.1 continuam abrindo normalmente na v1.2. Quando a propriedade `label_dx_pt` não existe, a posição horizontal é assumida como **0 pt** (centralizada na linha). Ao salvar novamente pela v1.2, a propriedade é gravada em cada anotação. O esquema do JSON permanece `pl-spectrum-viewer-plot-session/v1` por compatibilidade; os dados brutos continuam separados.


### Testes v1.3

Os **29 testes** automatizados passaram em ambiente sem interface (incluindo leitura instrumental, máximo discreto, fatores independentes, multiplicação não destrutiva, CSVs e PDFs/SVGs vetoriais). A execução da janela PySide6 deve ser verificada no Windows.
