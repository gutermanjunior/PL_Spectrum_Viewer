# PL Spectrum Viewer — v1.4 · Edição de figuras, unidades e legendas

**Data:** 13/10/2026. **Base:** PL Spectrum Viewer v1.3.2. **Escopo:** evolução incremental do aplicativo local, sem alterar aquisições experimentais.

## O que mudou

### 1. Unidade de sinal corretamente identificada

Por confirmação do operador das medidas, **as séries de sinal estão em volts (V)**. Os valores instrumentais dos arquivos binários DTLG e `.dat` são carregados e preservados numericamente em **V**. No gráfico, escolha **Unidade Y → V** ou **mV** na aba **Gráfico / anotações**:

- Exibição em V: `Y_exibido = Y_bruto[V] × fator_da_série`.
- Exibição em mV: `Y_exibido = 1000 × Y_bruto[V] × fator_da_série`.
- As etiquetas de Y são **Sinal do lock-in (V)** ou **Sinal do lock-in (mV)**, conforme a escolha. O eixo vertical não traz a expressão “uncalibrated”.
- O campo `200mV` de um nome de arquivo continua descrevendo **o fundo de escala configurado no lock-in**, não a unidade do sinal armazenado; as duas informações nunca são confundidas.
- O controle anterior **Unidade X** continua alternando **nm ↔ Å** com `1 nm = 10 Å`. Os limites e as anotações verticais são convertidos/coerentes.
- Os *máximos* são calculados a partir dos pontos medidos (após o fator de visualização, quando aplicável), e sua leitura é apresentada na unidade Y escolhida.
- **CSV bruto e CSV ajustado** permanecem numericamente em **V**, independentemente da unidade de exibição; novas colunas identificadas como `sinal_bruto_V` e `sinal_multiplicado_V` foram adicionadas. Os cabeçalhos antigos foram mantidos como **aliases de compatibilidade** para processos de planilha legados (mas **não devem ser interpretados como contestação** da unidade V confirmada pelo operador).

**Modo normalizado:** permanece uma opção separada, com Y adimensional. Trocar V/mV não modifica o valor das curvas normalizadas. É responsabilidade do operador ajustar os limites de Y quando alternar entre um gráfico bruto e um normalizado.

### 2. Anotações horizontais que acompanham a unidade

A anotação horizontal inserida no modo bruto guarda a coordenada em **V** no JSON, independentemente de o eixo mostrar V ou mV. Exemplo: uma referência a **0,032 V** será desenhada em **32 mV** após a troca para mV, sem mover a posição física. Anotações já salvas em JSON pela v1.3.2 são interpretadas como V, conforme a confirmação atual da unidade das aquisições.

Para evitar uma mistura dimensional, anotações horizontais criadas no modo **normalizado** são identificadas como adimensionais. Referências em V não aparecem sobre o eixo adimensional, nem referências normalizadas sobre o eixo em V/mV; ambas continuam preservadas no arquivo de edição. Anotações verticais funcionam nos três modos, inclusive com nm/Å. Clique, arraste, rótulos e deslocamentos continuam disponíveis.

### 3. Formatação científica avançada

Em **Gráfico / anotações → Aplicar formatação ao gráfico**, personalize:

| Categoria | Parâmetros |
| --- | --- |
| Figura | Largura e altura em polegadas (*in*), controlando proporção horizontal/vertical |
| Tipografia | Família: DejaVu Sans, DejaVu Serif, Liberation Sans, Liberation Serif ou STIXGeneral |
| Fontes | Título, subtítulo, nomes dos eixos, números dos eixos, legenda, anotações e nota inferior, com tamanhos independentes |
| Curvas | Espessura e estilo (contínua, tracejada, pontilhada, traço-ponto) |
| Guias | Espessura das linhas de referência vertical/horizontal |
| Grade | Opacidade (0–1) e espessura |
| Margens | Esquerda, direita, superior e inferior (frações da área da figura) |
| Subgráficos | Separação vertical entre curvas no modo de gráficos separados |
| Legenda | Posição, número de colunas, moldura e composição selecionável de campos |

A exportação PDF/SVG usa **a proporção definida na interface**, sem impor o tamanho fixo da versão anterior. Fontes aparecem vetorialmente no PDF e como elementos `<text>` no SVG (quando o software receptor suporta a família tipográfica). Arquivos PNG continuam disponíveis.

### 4. Campos selecionáveis na legenda

Marque os campos desejados, nesta ordem predefinida de apresentação:

- **Amostra**, inclusive o código auxiliar entre parênteses quando houver;
- **Fendas** (µm) indicadas no nome do arquivo;
- **Temperatura indicada** no nome do arquivo (K), sem afirmar sua confirmação por termometria;
- **Fundo de escala do lock-in** (mV), que **não** é a unidade Y;
- **Data e hora indicadas** no nome;
- **Fator multiplicativo** (`×f`) quando diferente de 1;
- **Nome completo do arquivo**.

Você pode escolher qualquer subconjunto, bem como posição, moldura e quantidade de colunas. O campo que **não aparece** no nome do arquivo não recebe valor inventado nem é sobrescrito por metadados internos divergentes. Sem campos aproveitáveis selecionados, o nome do arquivo serve de identificador de segurança da curva. As cores permanecem na ordem em que os gráficos foram marcados, como na v1.3.1.

## Uso da interface

1. Abra a pasta ou ZIP de medições e marque as curvas na ordem desejada.
2. Acesse **Gráfico / anotações** e altere **Unidade X** (nm ou Å) e **Unidade Y** (V ou mV).
3. Ajuste título, subtítulo, tamanhos de fonte, proporção, margens, espessuras e grade.
4. Na seção **Composição da legenda**, marque somente as características que devem aparecer. Defina posição/colunas.
5. Clique **Aplicar formatação ao gráfico** para redesenhar.
6. Exporte como PDF/SVG (figuras) e/ou **Salvar edição…** (JSON para reabrir e editar).

## Compatibilidade e limitações

- São aceitos arquivos JSON v1.1–v1.3.2, com fatores e ordem de seleção preservados. O texto-padrão antigo de Y é atualizado para **Sinal do lock-in**; rótulos personalizados do pesquisador são preservados.
- Os sinais continuam sendo medições instrumentais, e a simples conversão V↔mV não constitui calibração absoluta de intensidade luminosa, responsividade ou eficiência quântica.
- A escolha de família tipográfica é gravada no JSON, mas a disponibilidade dessas fontes precisa ser confirmada no computador Windows que executa o programa.
- Nenhuma medida de PL foi alterada ou reprocessada. Não há extração automática de índices ou identificações físicas de picos.
- Testes de núcleo e exportação realizados sem GUI. O **PySide6** não estava disponível neste ambiente e **o funcionamento da interface gráfica precisa ser validado no Windows**. Não há executável `.exe` pré-compilado.

Os exemplos reproduzíveis com as amostras #4574/#4575/#4576 de 09/10/2026 estão em `exemplos/v1_4_unidades_e_formatacao/`, em duas apresentações da mesma aquisição: **Å/mV** e **nm/V**. Regeneração: `python gerar_exemplo_v14.py`.
