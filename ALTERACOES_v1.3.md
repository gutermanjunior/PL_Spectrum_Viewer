# PL Spectrum Viewer — alterações v1.3

**Data:** 13/10/2026. **Base:** `PL_Spectrum_Viewer_v1_2_Deslocamento_Horizontal.zip`.

## 1. Localizar máximo de uma série

No painel esquerdo, destaque **uma linha** da tabela de aquisições e clique em **Localizar máximo**. O aplicativo:

- determina o máximo **global, discreto, nos pontos adquiridos** (sem interpolação, ajuste de pico, subtração de fundo ou calibração);
- mostra o valor do sinal multiplicado pelo fator da série e o comprimento de onda do ponto correspondente nas unidades do eixo (`nm` ou `Å`);
- mostra o valor bruto nesse ponto e, quando o fator difere de 1, o máximo bruto global separadamente;
- assinala o máximo único por um marcador circular e rótulo na curva do gráfico (incluído também em PDF/SVG);
- quando vários pontos empatam (por exemplo, todos zerados por fator `0`), informa o número de empates e não desenha um marcador de pico único.

O botão **Limpar destaque** remove apenas a marcação do pico. Se a curva estiver desmarcada, o comando de máximo a marca para que apareça no gráfico. O resultado é **global**, mesmo com limites de X restringindo a visualização; ajuste os limites para ver um ponto fora da região visível.

## 2. Multiplicação independente de cada série

Destaque uma aquisição na tabela, escolha **Multiplicar sinal por** (padrão `1`) e clique em **Aplicar fator**. Para desfazer, use **Restaurar ×1**. O fator pode ser positivo, negativo ou zero, é adimensional, finito e limitado a `[-10^6, +10^6]` para prevenir erros numéricos; a interface aceita oito casas decimais.

- Apenas a aquisição destacada recebe o fator (não as demais curvas marcadas).
- O fator altera somente a série exibida e a figura exportada. **A matriz bruta em memória e os arquivos DTLG/DAT/CSV originais nunca são sobrescritos.**
- A legenda exibe `[×f]` quando `f ≠ 1`. Fatores podem ser aplicados a várias séries, cada qual independentemente.
- No modo **sobreposição normalizada**, o aplicativo usa a amplitude absoluta máxima **após** multiplicação; fatores positivos uniformes de uma série deixam sua forma normalizada igual. Para estudar diferenças de altura, use o modo de sinal bruto.
- Valores de pico são reportados **antes da normalização**, mesmo se a visualização estiver normalizada.

## 3. Exportação de dados com proveniência

- **Exportar CSV bruto** mantém a exportação anterior exclusivamente dos pontos medidos.
- **Exportar CSV ajustado** cria um arquivo separado com o valor bruto, o fator adimensional e o sinal multiplicado, além de λ e identidade da aquisição. Nunca substitui os arquivos de origem.
- PDF/SVG mostram as curvas ajustadas, legenda `[×f]`, anotações e marcador de máximo, todos vetoriais.
- **Salvar edição** inclui `spectrum_display_factors` e `highlight_peak_uid` no arquivo JSON já usado pela v1.1/v1.2 (mesmo esquema de sessão v1). **Abrir edição** restaura os fatores apenas quando a fonte corresponde àquela salva; os JSONs antigos sem campos novos continuam válidos, assumindo fatores 1 e nenhum pico destacado.

## 4. Exemplo incluído

Execute `python gerar_exemplo_v13.py`. Os resultados já acompanham o ZIP em `exemplos/v1_3_maximo_e_fatores/`: PDF, SVG, PNG e JSON da edição.

Usa as três aquisições de 300 µm / 200 mV de 09/10/2026. Demonstra fator `2` somente na #4576 e máximo discreto assinalado na #4575. **O exemplo ilustra processamento visual; não estabelece razões de eficiência quântica entre amostras.**

## 5. Verificação e limites

- **29 testes automatizados passaram**, cobrindo leitores antigos, fatores por UID, não mutação do sinal, escala negativa/zero, máximo real discreto, compatibilidade do JSON, CSV ajustado e vetorial PDF/SVG.
- PDF do exemplo verificado com PyMuPDF: texto presente, dezenas de elementos desenhados, nenhuma imagem raster.
- Interface PySide6 **não executada neste ambiente** (biblioteca indisponível). Recomenda-se abrir/testar no Windows, verificar os controles, alternância de seleção e exportação pelo diálogo antes de adotar a versão em rotina experimental.
