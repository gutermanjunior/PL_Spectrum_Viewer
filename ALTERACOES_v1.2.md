# PL Spectrum Viewer v1.2 — deslocamento horizontal dos rótulos

**Data:** 13/10/2026. **Base:** `PL_Spectrum_Viewer_v1_1_Anotacoes_Vetorial.zip`, mantido como versão anterior independente.

## Novo

- Campo **Rótulo: ← / →** no editor de anotações, intervalo **−240 a +240 pt**, passos de **5 pt**, início em **0 pt**.
- Valor negativo move apenas o texto para a esquerda; positivo para a direita; zero mantém o texto centralizado sobre a linha.
- Coordenada da linha vertical e seu comprimento de onda permanecem inalterados.
- Deslocamento expresso em pontos tipográficos, não em nm ou Å; estável após conversão de unidades, zoom e exportação vetorial.
- Cada anotação mantém deslocamento próprio; o valor é restaurado ao selecionar a linha e salvo no arquivo JSON de edição.
- Sessões JSON v1.1 são lidas com deslocamento padrão igual a zero, preservando compatibilidade.
- Exemplos vetoriais das amostras #4574–#4576 atualizados com deslocamentos à esquerda e à direita.

## Verificações

- Testes headless de deslocamento em tela, equivalência nm/Å, limites de valor, exportação PDF/SVG e persistência de sessão.
- O aplicativo PySide6 ainda precisa ser validado interativamente em Windows; não há `.exe` nesta distribuição.
- A renderização não modifica os dados medidos nem estabelece atribuições físicas automáticas.
