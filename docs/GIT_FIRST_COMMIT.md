# Primeiro commit — PL Spectrum Viewer v1.5

## Contexto

Pasta Windows informada: `C:\Users\Guterman\GitHub\PL_Spectrum_Viewer`.

O GitHub Desktop já foi utilizado para inicializar o repositório local, mas o usuário informou ter usado **Undo** no *Initial Commit*. O estado atual deve ser verificado: **não presuma que não existe nenhum commit** até consultar `git status` e `git log`.

**Nome remoto recomendado:** `pl-spectrum-viewer`; a pasta local pode continuar com o nome antigo. **Visibilidade inicialmente recomendada:** privada, até conferência de autoria, autorização de compartilhamento e dados das campanhas.

## 1. Preparar a cópia local

1. Feche processos que estejam modificando arquivos da pasta durante a revisão.
2. Faça backup dos `README.md` e `.gitignore` existentes (se presentes).
3. Copie para a raiz do projeto, a partir do kit de documentação:
   - `README.md` (substituir o README original **somente depois de compará-lo**);
   - `CHANGELOG.md` (novo);
   - `.gitignore` (mesclar com regras existentes, se necessário);
   - `docs/GIT_FIRST_COMMIT.md` (novo).
4. **Mantenha** os arquivos `ALTERACOES_v*.md` e `BUILD_INFO_v*.txt`, pois registram a proveniência documental das versões.
5. Revise `assets/` (presente na pasta local, mas não necessariamente no ZIP original), scripts auxiliares e qualquer arquivo de configuração local.
6. Avalie se `VALIDACAO_DADOS.txt` inclui resultados experimentais que não podem ser divulgados; caso haja dúvida, mantenha privado e não inclua no commit público.

## 2. Verificar Git e arquivos ignorados

Abra o PowerShell na raiz do projeto:

```powershell
git status
git log -1 --oneline
git remote -v
git status --short --untracked-files=all
```

`git log` pode avisar que a branch **ainda não possui commits**; isso é esperado caso o Undo tenha removido o commit inicial. Se houver outros commits, **não apague o histórico** sem revisar.

Confirme a exclusão do ambiente virtual:

```powershell
git check-ignore -v .venv/Scripts/python.exe
```

Se o ambiente virtual já tiver entrado em algum commit anterior, o `.gitignore` sozinho **não o remove do histórico**; é necessário avaliar o estado já versionado antes de publicar.

**Ponto crítico:** o `.gitignore` deste kit exclui `exemplos/` por precaução. Porém, vários testes usam o ZIP experimental localizado nessa pasta. **Não anuncie que todos os testes são reproduzíveis num clone sem os dados**, até que os testes sejam adaptados para fixtures sintéticas ou que a distribuição do conjunto de teste seja autorizada.

## 3. Verificação local

Ative a `.venv` ou use o interpretador diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests
```

Antes da publicação, confirme: nenhum token, senha, chave de API, e-mail privado, documento institucional restrito, relatório com metadados sensíveis ou medição não autorizada entra no commit. O GitHub Desktop permite abrir o diff de **cada** arquivo em *Changes*.

## 4. Primeiro commit pelo GitHub Desktop

1. Abra o repositório local no GitHub Desktop.
2. Em **Changes**, revise os caminhos e o conteúdo dos arquivos selecionados.
3. Certifique-se de que `.venv/`, `__pycache__/` e `exemplos/` **não aparecem**.
4. Use o Summary e Description sugeridos abaixo.
5. Clique **Commit to main** (se o ramo atual realmente for `main`).
6. Após confirmar o conteúdo do commit em **History**, clique em **Publish repository**.
7. Use o nome remoto `pl-spectrum-viewer` e mantenha a opção **Keep this code private** ativada.

### Summary

```text
chore: import PL Spectrum Viewer v1.5 baseline
```

### Description

```text
Import the existing PL Spectrum Viewer v1.5 Python application as the first
version-controlled baseline.

- Preserve the v1.4.1 responsive preview fix and v1.5 multi-panel plotting.
- Include source modules, tests, dependencies and Windows launch scripts.
- Add a detailed README, consolidated CHANGELOG and Git ignore rules.
- Preserve version history as documentation, not fabricated Git commits.
- Exclude virtual environments, caches, builds and unreviewed datasets.

Validation: 78 headless tests passed against the original v1.5 data package.
Interactive PySide6/Windows GUI validation remains pending.
```

> **Ajuste necessário:** se os 78 testes **não forem executados novamente no seu computador**, troque a última linha de validação para `Validation: 78 headless tests passed in the documentation preparation environment; local Windows test pending.`. Não reporte um teste local que não foi executado.

## 5. Depois de publicar

- Confira se o GitHub remoto exibe o README renderizado e os arquivos esperados.
- Verifique **Settings → General → Default branch** e use `main`, se esse for o ramo adotado.
- Crie uma tag `v1.5.0` **apenas quando decidir formalizar esta entrega como release**.
- Se necessário, anexe o ZIP de distribuição revisado a **Releases**, em vez de versionar cópias completas do código no histórico.
- Para desenvolvimento futuro, use branches pequenas (`feature/...`, `fix/...`) e commits com intenção explícita.
- Para cada commit futuro, documente **Summary** e **Description** antes de confirmar.

## 6. Decisões em aberto

- Autorização para publicar dados experimentais e figuras reais: **não assumida**.
- Origem e licenciamento de eventuais recursos em `assets/`: **não inspecionados na cópia Windows**.
- Licença open source: **não definida** (não gerar automaticamente `LICENSE`).
- Reprodutibilidade dos testes sem dados reais: **pendência técnica reconhecida**.
- Verificação prática da GUI no Windows: **pendente**.

Fontes oficiais: https://docs.github.com/en/desktop/overview/creating-your-first-repository-using-github-desktop ; https://docs.github.com/en/desktop/managing-commits/options-for-managing-commits-in-github-desktop
