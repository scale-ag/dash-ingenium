# Configuração do cron-job.org

O workflow `.github/workflows/deploy.yml` roda na `main` a cada push em `build/**`,
a cada disparo `workflow_dispatch` (cron-job.org) e por um `schedule` nativo de
backup (`*/30 * * * *`). Página publicada em:

**`https://scale-ag.github.io/dash-ingenium/`**

## Token do GitHub (fine-grained)

GitHub → *Settings* → *Developer settings* → **Fine-grained tokens** → *Generate*:
- Resource owner: **scale-ag**
- Repository access: **Only select repositories → `dash-ingenium`**
- Permissions → **Actions: Read and write**

O token vai **só** no cron-job.org (nunca no repositório). Se for exposto, revogue e gere outro.

## Cron job (https://cron-job.org)

### URL
```
https://api.github.com/repos/scale-ag/dash-ingenium/actions/workflows/deploy.yml/dispatches
```

### Método
```
POST
```

### Schedule
```
Every 30 minutes
```

### Headers (cadastre cada um: chave e valor em campos separados)

| Chave | Valor |
|---|---|
| `Accept` | `application/vnd.github+json` |
| `Authorization` | `Bearer TOKEN_AQUI` |
| `X-GitHub-Api-Version` | `2022-11-28` |
| `Content-Type` | `application/json` |

### Request body
```
{"ref":"main"}
```

## Como saber se funcionou

- Resposta esperada: **HTTP 204 No Content**.
- 401/403 = token errado ou sem **Actions: write** · 404 = owner/repo/arquivo errado ·
  422 = workflow não está na `main`.
