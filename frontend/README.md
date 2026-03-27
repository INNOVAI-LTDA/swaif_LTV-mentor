# Frontend MVP Mentoria

Bootstrap inicial do novo frontend executavel em React + Vite.

## Requisitos

- Node 18+
- npm 9+

## Setup

```bash
npm install
```

## Desenvolvimento

```bash
npm run dev
```

Para desenvolvimento local, use `VITE_DEPLOY_TARGET=local`. Nesse alvo, o frontend ainda pode assumir `http://127.0.0.1:8000` quando `VITE_API_BASE_URL` nao estiver definido.

## Build

```bash
npm run build
```

Todo build agora exige `VITE_DEPLOY_TARGET`. Em builds `client`, `VITE_CLIENT_CODE` e `VITE_API_BASE_URL` passam a ser obrigatorios. `VITE_API_BASE_URL` precisa ser uma URL absoluta `http(s)` sem credenciais, query strings ou fragments.

## Testes

```bash
npm run test
```

## Ambiente

Copie `.env.example` para `.env` e ajuste:

- Para clientes ja parametrizados no repo, prefira o template especifico correspondente, por exemplo `.env.client.accmed.example`.
- O template generico continua sendo o fallback para novos clientes.

- `VITE_API_BASE_URL`
- `VITE_HTTP_TIMEOUT_MS`
- `VITE_APP_BASE_PATH`
- `VITE_DEPLOY_TARGET`
- `VITE_CLIENT_CODE`
- `VITE_CLIENT_NAME`
- `VITE_APP_NAME`
- `VITE_APP_TAGLINE`
- `VITE_ENABLE_DEMO_MODE`
- `VITE_ENABLE_INTERNAL_MENTOR_DEMO`

### Contrato de ambiente

- `VITE_DEPLOY_TARGET`: define a intencao do build. Use `local` para desenvolvimento e `client` para build publicado.
- `VITE_CLIENT_CODE`: identificador explicito do cliente ativo. Obrigatorio para builds `client` e deve corresponder ao `CLIENT_CODE` do backend no mesmo deploy.
- `VITE_API_BASE_URL`: URL base explicita da API. Obrigatoria para builds de cliente.
- `VITE_API_BASE_URL` deve ser uma origem/caminho absoluto `http(s)` sem credenciais, query strings ou fragments.
- `VITE_HTTP_TIMEOUT_MS`: timeout do cliente HTTP em milissegundos.
- `VITE_APP_BASE_PATH`: subpath de deploy do frontend. Use `/` na raiz ou valores como `/cliente/mentoria/`.
- `VITE_CLIENT_NAME`: nome do cliente mostrado em shell, login e identidade visual principal.
- `VITE_APP_NAME`: nome do produto mostrado no navegador e nos shells.
- `VITE_APP_TAGLINE`: mensagem curta usada nas superficies de entrada e navegacao.
- `VITE_SHELL_SUBTITLE`: subtitulo reservado para shells e comunicacao institucional da interface.
- `VITE_BRANDING_ICON_PATH`, `VITE_BRANDING_LOGO_PATH`, `VITE_BRANDING_LOGIN_HERO_PATH`: caminhos publicos dos ativos de branding.
- `VITE_THEME_*`: tokens opcionais de cor para aplicar o branding do cliente sem editar CSS base.
- `VITE_ENABLE_DEMO_MODE`: liga o modo demo interno que reexibe o login preview. O padrao operacional deve ser `false`.
- `VITE_ENABLE_INTERNAL_MENTOR_DEMO`: flag de compatibilidade para validacao interna ligada ao legado das rotas `mentor-demo`. Ela nao bloqueia mais o workspace publicado de mentor nesta entrega.
- Em builds de cliente, `VITE_ENABLE_DEMO_MODE` e ignorado para evitar exposicao acidental do fluxo preview.
- Em builds de cliente, `VITE_ENABLE_INTERNAL_MENTOR_DEMO` deixa de ser um gate funcional para a navegacao publicada de mentor.

### Contrato atual para Vercel (Batch B)

- O deploy atual preparado para Vercel usa raiz do dominio: `VITE_APP_BASE_PATH=/`.
- Configure a `Root Directory` do projeto Vercel como `frontend`.
- Use os exemplos versionados para separar ambientes:
  - `frontend/.env.preview.example` (Vercel Preview)
  - `frontend/.env.production.example` (Vercel Production)
- O app continua suportando subpath, mas isso nao e o padrao operacional do deploy Vercel atual.

### Deploy sob subpath

- O router usa `basename` configuravel por `VITE_APP_BASE_PATH`.
- Os assets de branding tambem passam a respeitar esse base path.
- Se o frontend for publicado em um subdiretorio, configure o mesmo valor no ambiente e nas regras do host.
- O backend publicado precisa do par `APP_ENV` + `CORS_ALLOW_ORIGINS` alinhado com a origem real do frontend.
- Para o deploy Vercel atual, use `/` a menos que um batch posterior justifique subpath explicitamente.

### Fluxos seguros de build

Build local:

```bash
VITE_DEPLOY_TARGET=local npm run build
```

Build client-safe:

```bash
VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build
```

Template cliente AccMed:

Use este template apenas para validacao/bootstrap local. Para deploy hospedado no Vercel, siga o contrato atual em `DEPLOY.md` com `VITE_APP_BASE_PATH=/` e envs explicitos no host.

```bash
cp .env.client.accmed.example .env
npm run build
```

Bootstrap local por `client_code`:

```bash
scripts\mvp_bootstrap.bat --client-code accmed
```

Esse fluxo procura automaticamente:

- `frontend/.env.client.accmed` ou `frontend/.env.client.accmed.example`
- `backend/.env.client.accmed` ou `backend/.env.client.accmed.example`

Contrato operacional do bootstrap:

- `--client-code` precisa ser o mesmo valor para backend e frontend.
- O frontend precisa receber `VITE_CLIENT_CODE=<client_code>`.
- O backend precisa receber `CLIENT_CODE=<client_code>`.

Backend correspondente:

```bash
APP_ENV=production CLIENT_CODE=accmed CORS_ALLOW_ORIGINS=https://cliente.example.com py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Exemplos invalidos que devem falhar:

- `npm run build` sem `VITE_DEPLOY_TARGET`
- `VITE_DEPLOY_TARGET=client` sem `VITE_CLIENT_CODE`
- `VITE_DEPLOY_TARGET=client` sem `VITE_API_BASE_URL`
- `VITE_DEPLOY_TARGET=client VITE_API_BASE_URL=api.example.com`
- `VITE_DEPLOY_TARGET=client VITE_API_BASE_URL=https://api.example.com?tenant=x`
- `APP_ENV=production CORS_ALLOW_ORIGINS=https://cliente.example.com/app`
- `APP_ENV=production` sem `CLIENT_CODE`

### Demo mode

- `loginPreview` foi mantido apenas para demonstracoes internas.
- Em ambiente de cliente, mantenha `VITE_ENABLE_DEMO_MODE=false`.
- Em ambiente de cliente, mantenha `VITE_ENABLE_INTERNAL_MENTOR_DEMO=false`.
- Com demo mode desligado, a tela de login nao deve expor credenciais ou atalhos preview ao cliente final.
- Com `VITE_ENABLE_INTERNAL_MENTOR_DEMO=false`, o login de mentor continua funcional no workspace publicado. A flag fica restrita a compatibilidade com validacoes internas e nao deve negar o acesso normal do mentor.

### Recuperacao de sessao

- `AUTH_BOOTSTRAP_RETRYABLE` significa que o login concluiu, mas a validacao de `/me` falhou temporariamente.
- Nessa situacao, a tela de login mostra uma faixa de recuperacao com `Tentar novamente` e `Limpar sessao`.
- Use `Tentar novamente` quando o backend voltar e voce quiser reaproveitar a sessao autenticada.
- Use `Limpar sessao` quando quiser descartar o token pendente e reiniciar o acesso do zero.

### Pareamento com backend

- Em deploys reais, configure `APP_ENV` com um valor nao local no backend.
- Defina `CORS_ALLOW_ORIGINS` com a origem publicada do frontend, sem depender dos defaults localhost.
- `CORS_ALLOW_ORIGINS` deve conter apenas origins puras, como `https://cliente.example.com`, sem credenciais, caminhos, query strings ou fragments.
- Nao considere o deploy concluido se apenas as variaveis do frontend estiverem configuradas.

### Artefatos de release

- Gate operacional da release: `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- Runbook operacional: `docs/client-launch-runbook.md`
- Tracker de release: `docs/production-release-tracker.md`
- Contrato operacional Vercel deste batch: `DEPLOY.md`

### Postura atual de piloto

- A persistencia do backend ainda e baseada em arquivos JSON locais. Trate a release atual como operacao de servidor unico ate que a estrategia de banco de dados seja definida.
- Antes de qualquer staging remoto, execute um snapshot local com `py -m app.operations.storage_maintenance backup` e valide um restore com `py -m app.operations.storage_maintenance restore <snapshot_dir>`.
- O backend agora registra no startup o resumo operacional de `app_env`, `cors_origins`, `mentor_demo_routes`, `storage_root` e `backup_dir`. Capture esse log como evidencia antes do deploy remoto.
- O workspace de mentor agora faz parte da superficie publicada. Mantenha `VITE_ENABLE_INTERNAL_MENTOR_DEMO=false` como padrao operacional e trate qualquer dependencia restante do legado `mentor-demo` apenas como compatibilidade tecnica, nao como bloqueio funcional do mentor.
