# Changelog — PL Spectrum Viewer

Histórico **documental** consolidado a partir dos arquivos `ALTERACOES_v*.md` disponíveis na distribuição v1.5. **Não representa commits Git históricos**: o versionamento do repositório começa a partir da importação do estado existente. Datas indicam o registro na documentação de origem, não necessariamente a execução original de cada modificação.

## [1.5] — 2026-10-14

- Composições `1×1`, `1×2`, `2×1` e `2×2`, com séries, limites, legendas, títulos e anotações por painel.
- Controles de eixos compartilhados quando compatíveis; espaçamento horizontal e vertical ajustável.
- Caixas independentes para mostrar ou ocultar título, subtítulo e nota inferior, **recuperando o espaço**.
- Sessões JSON persistem a composição, inclusive painéis temporariamente não visíveis.
- Preservada a pré-visualização responsiva da v1.4.1 e a separação das dimensões de exportação.
- **Registro de validação:** 78 testes automatizados headless; GUI não testada interativamente na distribuição de origem.

Detalhes: [`ALTERACOES_v1.5.md`](ALTERACOES_v1.5.md).

## [1.4.1] — 2026-10-13

- Correção de figura que ultrapassava o painel central.
- Pré-visualização com tamanho governado pela área Qt, não pelas polegadas configuradas para saída.
- Exportação realizada com figura separada; preservadas opções de formatação e os dados originais.

Detalhes: [`ALTERACOES_v1.4.1.md`](ALTERACOES_v1.4.1.md).

## [1.4] — 2026-10-13

- Confirmação pelo operador de sinal bruto em **V**; alternância de exibição **V/mV**.
- Alternância **nm/Å** em X; anotações convertidas conforme escala de apresentação.
- Editor avançado de dimensões, fontes, traços, grade, margens e legendas por campos selecionáveis.
- Persistência e compatibilidade de sessões anteriores.

Detalhes: [`ALTERACOES_v1.4.md`](ALTERACOES_v1.4.md).

## [1.3.2] — 2026-10-13

- Anotações horizontais no sinal Y, além das linhas verticais.
- Nome atual do arquivo passa a prevalecer na identificação da aquisição (amostra, fendas, T indicada e fundo de escala); cabeçalhos preservados para comparação.
- Reconhecimento de identificadores auxiliares como `4557(1659)` e de campos ausentes.

Detalhes: [`ALTERACOES_v1.3.2.md`](ALTERACOES_v1.3.2.md).

## [1.3.1] — 2026-10-13

- Cores e ordem de legenda determinadas pela ordem efetiva de marcação dos espectros; desmarcar/remarcar envia a curva ao final.
- Ordem persistida em JSON.

Detalhes: [`ALTERACOES_v1.3.1.md`](ALTERACOES_v1.3.1.md).

## [1.3] — 2026-10-13

- Localização do valor máximo **discreto** e comprimento de onda da série selecionada.
- Fatores multiplicativos por curva, sem alteração do sinal bruto.
- Exportações que distinguem valores instrumentais e valores ajustados.

Detalhes: [`ALTERACOES_v1.3.md`](ALTERACOES_v1.3.md).

## [1.2] — 2026-10-13

- Deslocamento horizontal independente dos rótulos das anotações verticais, medido em pontos tipográficos.
- Preservação do posicionamento em sessões JSON e figuras vetoriais.

Detalhes: [`ALTERACOES_v1.2.md`](ALTERACOES_v1.2.md).

## [1.1] — 2026-10-13

- Edição científica de figuras; linhas de referência verticais, títulos, limites e anotações.
- Exportação vetorial PDF/SVG e persistência JSON da formatação.
- Leitura de DTLG/DAT/CSV/ZIP e verificações de duplicatas preservadas do MVP.

Detalhes: [`ALTERACOES_v1.1.md`](ALTERACOES_v1.1.md).

## [MVP] — data de origem não estabelecida neste changelog

- Base prévia do leitor/visualizador; consulte os arquivos originais de proveniência antes de atribuir data, autoria ou funcionalidades adicionais.

---

### Integridade histórica

Os documentos `ALTERACOES_v*.md` e `BUILD_INFO_v*.txt` permanecem como fontes de detalhe, dependências, limites de validação e decisões originais. Para mudanças **posteriores ao primeiro commit**, use novos registros datados e mensagens Git objetivas. Não represente a importação retrospectiva como commits efetivamente realizados nas datas acima.
