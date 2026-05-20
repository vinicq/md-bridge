# Contribuindo no md-bridge: fork → claim → PR

Passo a passo completo pra quem nunca contribuiu num projeto open source no
GitHub. Funciona pra qualquer projeto que aceite PRs via fork, mas os exemplos
usam o `md-bridge`. Substitua o owner/repo conforme o caso.

## Pré-requisitos

- Conta no GitHub
- `git` instalado
- `gh` (GitHub CLI) opcional, mas economiza cliques

## 1. Fork do repositório

Um fork é a sua cópia pessoal do projeto. Você empurra commits pro fork, não
pro repo original, e abre PR a partir dele.

### Pela UI

1. Acesse <https://github.com/vinicq/md-bridge>
2. Clique em **Fork** no canto superior direito
3. Deixe "Copy the `main` branch only" marcado
4. Confirme

Resultado: `https://github.com/SEU_USUARIO/md-bridge` aparece na sua conta.

### Pela CLI

```bash
gh repo fork vinicq/md-bridge --clone=false
```

## 2. Clone do seu fork e configuração de remotes

```bash
git clone https://github.com/SEU_USUARIO/md-bridge.git
cd md-bridge
git remote add upstream https://github.com/vinicq/md-bridge.git
git remote -v
```

A saída esperada:

```
origin    https://github.com/SEU_USUARIO/md-bridge.git (fetch)
origin    https://github.com/SEU_USUARIO/md-bridge.git (push)
upstream  https://github.com/vinicq/md-bridge.git (fetch)
upstream  https://github.com/vinicq/md-bridge.git (push)
```

- `origin` é o seu fork (onde você empurra)
- `upstream` é o repo do mantenedor (de onde você puxa atualizações)

## 3. Escolha uma issue e leia o escopo

Filtros úteis:

- Boas pra primeira contribuição: <https://github.com/vinicq/md-bridge/issues?q=is:open+label:%22good+first+issue%22>
- Aceitando ajuda: <https://github.com/vinicq/md-bridge/issues?q=is:open+label:%22help+wanted%22>

Antes de comentar:

1. Leia o body inteiro da issue (Context, Architect notes, QA notes, Acceptance criteria)
2. Confira se alguém já comentou pedindo a issue. Se sim, espere o assignee desistir
3. Confira se a branch protection e os checks obrigatórios fazem sentido pro seu setup

## 4. Faça o claim

A regra do projeto: comentar primeiro, codar depois. Isso evita duas pessoas
trabalhando na mesma coisa sem saber.

### Fluxo automatizado: `/claim`

Comente na issue:

```
/claim
```

Sozinho, num comentário. A Action `Issue claim` adiciona a label
`status: claimed`, te marca como assignee (se você for collaborator), posta
um comentário com o deadline e move o card pra coluna "Claimed" no board do
projeto. Sem espera por mantenedor.

> **Caveat pra externos:** GitHub não permite atribuir issue a quem não é
> collaborator do repo. Pra externos, a Action posta um comentário de
> atribuição em vez de setar o assignee. O efeito prático é o mesmo: o nome
> fica registrado, a label é aplicada, o card é movido no board.

`/take` funciona como alias.

A partir do momento da confirmação, a issue é sua por **7 dias**.

## 5. Crie a branch local

A partir do `main` atualizado:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git checkout -b feat/N-resumo-curto
```

Convenções de nome de branch:

- `feat/14-theme-picker` pra feature
- `fix/27-drag-reorder-crash` pra bug
- `docs/26-api-recipes` pra doc
- `chore/30-codecov` pra infra

O número casa com a issue. O slug é curto e direto.

## 6. Trabalhe e commite

Conventional Commits 1.0.0 é obrigatório. Subject minúsculo:

```bash
git add caminho/do/arquivo
git commit -m "feat(web): add theme picker dropdown to /md-to-pdf"
```

Tipos válidos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`,
`ci`, `build`, `style`, `revert`.

Rode os testes localmente antes de empurrar:

```bash
# Backend
cd apps/api && uv run pytest

# Web
cd apps/web && npm test

# E2E (mais lento)
cd apps/web && npx playwright test
```

## 7. Push pro seu fork

```bash
git push origin feat/N-resumo-curto
```

A saída inclui um link `Create a pull request for ...`. Clique nele ou abra o
PR pela CLI.

## 8. Abra o PR pelo template

### Pela UI

1. <https://github.com/SEU_USUARIO/md-bridge>
2. Clique no banner amarelo "Compare & pull request"
3. Confira que o base é `vinicq/md-bridge:main` e o head é
   `SEU_USUARIO/md-bridge:feat/N-resumo-curto`
4. Preencha o template (Summary, Test plan)
5. Inclua `Closes #N` no body pra fechar a issue ao merge

### Pela CLI

```bash
gh pr create \
  --repo vinicq/md-bridge \
  --base main \
  --title "feat(web): add theme picker dropdown to /md-to-pdf" \
  --body "Closes #24

  ## Summary
  - Adds the theme picker dropdown bound to options.theme.
  - Wires the GET /api/themes call to populate the menu.

  ## Test plan
  - [x] Vitest covers the dropdown render and the onChange handler.
  - [x] Playwright covers the theme switch and the PDF preview update."
```

## 9. Revisão e mudanças

O CI roda automaticamente. Os checks bloqueantes são:

- `Backend (pytest)`
- `Web (vitest + build)`
- `End-to-end (Playwright)`
- `CodeQL (python)`, `CodeQL (javascript-typescript)`
- `Validate PR title`

Se algum quebrar, leia o log, conserte, commite no mesmo branch, dê push. O PR
atualiza sozinho.

Quando o mantenedor pedir mudanças:

```bash
# faça os edits
git add .
git commit -m "fix(web): handle empty theme list gracefully"
git push origin feat/N-resumo-curto
```

Não force-push se já tem review em cima. Adicione commits novos, eles viram um
só no squash merge.

## 10. Merge e crédito

O merge é squash. Seu nome vira o autor do commit final no `main`.

Depois do merge:

1. O mantenedor adiciona você no `.all-contributorsrc` com as categorias
   relevantes (`code`, `doc`, `test`, `infra`, `translation`, etc.)
2. O README é regenerado e seu avatar aparece na seção Contributors
3. Se a issue tinha `Closes #N`, ela fecha sozinha e a Action
   `pr-linked-issue` posta atribuição lá

## Resumo num quadro

| Passo | Onde | O que acontece |
|---|---|---|
| Fork | GitHub UI | Cópia do repo na sua conta |
| Clone | Terminal | Diretório local com `origin` (fork) e `upstream` (original) |
| Claim | Comentário `/claim` na issue | Action aplica label, assigna, move o card, posta deadline |
| Branch | Terminal | `git checkout -b feat/N-slug` |
| Commit | Terminal | Conventional Commits 1.0.0 |
| Push | Terminal | `git push origin feat/N-slug` |
| PR | GitHub UI ou `gh pr create` | Base = `vinicq/md-bridge:main` |
| Revisão | Comentários no PR | Commit e push no mesmo branch |
| Merge | Mantenedor faz | Squash merge |
| Crédito | `.all-contributorsrc` | Auto-update após merge |

## Erros comuns

- **Branch errada no PR:** se você abriu o PR contra
  `SEU_USUARIO/md-bridge:main` em vez de `vinicq/md-bridge:main`, edite o base
  na UI do PR.
- **Conflito com `main`:** rode `git fetch upstream && git merge upstream/main`
  na sua branch, resolva os conflitos, commite, dê push.
- **CI quebrado por hook local:** se o pre-commit travou no seu lado, leia o
  motivo. Não use `--no-verify`. O hook existe pra te poupar do CI falhar.
- **Squash apagou seus commits intermediários:** é esperado. O histórico é
  preservado no PR, só o `main` recebe um commit consolidado.
