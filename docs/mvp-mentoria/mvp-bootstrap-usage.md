# MVP Bootstrap (Local)

Script principal:
- `scripts/mvp_bootstrap.py`

Wrapper Windows:
- `scripts/mvp_bootstrap.bat`

## Objetivo

Subir backend e frontend (quando existir frontend executavel) com fluxo limpo:
- checa portas
- identifica PID/processo ocupando porta
- encerra processo automaticamente (exceto com `--no-kill`)
- sobe backend e valida healthcheck
- sobe frontend e valida abertura de porta quando houver frontend valido
- encerra tudo de forma organizada em falha ou `Ctrl+C`

## Uso rapido

## Windows

```bat
scripts\mvp_bootstrap.bat
```

## Linux/macOS

```bash
python scripts/mvp_bootstrap.py
```

## Opcoes principais

- `--no-kill`: nao encerra processos em portas ocupadas
- `--backend-only`: sobe apenas backend
- `--frontend-only`: sobe apenas frontend
- `--ports`: apenas inspeciona portas e sai
- `--frontend-dir "<caminho>"`: define raiz do frontend (onde existe `package.json`)
- `--backend-port <porta>`
- `--frontend-port <porta>`
- `--backend-cmd "<comando>"`
- `--frontend-cmd "<comando>"`

## Variaveis de ambiente suportadas

- `BACKEND_PORT` (default `8000`)
- `FRONTEND_PORT` (default `5173`)
- `BACKEND_HOST` (default `127.0.0.1`)
- `FRONTEND_HOST` (default `127.0.0.1`)
- `BACKEND_HEALTH_PATH` (default `/health`)
- `FRONTEND_DIR` (raiz do frontend com `package.json`)
- `BACKEND_CMD`
- `FRONTEND_CMD`
- `API_BASE_URL` / `VITE_API_BASE_URL` (injetadas para frontend quando script sobe ambos)

## Descoberta de frontend

Quando `--frontend-dir`/`FRONTEND_DIR` nao sao informados, o bootstrap tenta descobrir o frontend automaticamente:
- busca `package.json` dentro do repositorio
- exige `scripts.dev` valido
- ignora diretorios como `origin`, `backend`, `docs`, `test_tmp*`, `.tmp*`, `.localtmp*`, `node_modules`, `.venv`, `.vendor` e afins

Se nao encontrar frontend valido:

- `[INFO] frontend nao encontrado neste projeto`
- `[INFO] iniciando apenas o backend`

Neste caso, o script segue sem erro e nao executa `npm`.

## Exemplo com frontend fora da raiz padrao

```bash
python scripts/mvp_bootstrap.py --frontend-dir "..\\swaif_ltv_mentor\\frontend"
```

Se precisar forcar comando:

```bash
python scripts/mvp_bootstrap.py --frontend-dir "..\\swaif_ltv_mentor\\frontend" --frontend-cmd "npm run dev"
```

## Logs

Logs de processo ficam em:
- `.logs/mvp-bootstrap/backend.log`
- `.logs/mvp-bootstrap/frontend.log`

## Guia operacional

Para setup rapido em modo copiar/colar: `docs/mvp-mentoria/mvp-bootstrap-copy-paste.md`

