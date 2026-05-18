# Frontend App (portável)

Pacote portátil do frontend React + Vite + TypeScript strict para bootstrap em outro repositório.

## Arquivos incluídos

- `src/`
- `public/` (inclui `public/branding/*`)
- `index.html`
- `package.json`
- `package-lock.json`
- `tsconfig.json`
- `vite.config.ts`
- `.env.example`
- `.gitignore`

## Setup rápido

```bash
npm install
cp .env.example .env
```

## Build

Build local:

```bash
VITE_DEPLOY_TARGET=local npm run build
```

Build client-safe:

```bash
VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=<client_code> VITE_API_BASE_URL=https://<backend-domain> VITE_APP_BASE_PATH=/ npm run build
```

## Contrato de ambiente (resumo)

Obrigatórios para build `client`:

- `VITE_DEPLOY_TARGET=client`
- `VITE_CLIENT_CODE`
- `VITE_API_BASE_URL`

Branding/copy:

- `VITE_CLIENT_NAME`, `VITE_APP_NAME`, `VITE_APP_TAGLINE`, `VITE_SHELL_SUBTITLE`
- `VITE_BRANDING_ICON_PATH`, `VITE_BRANDING_LOGO_PATH`, `VITE_BRANDING_LOGIN_HERO_PATH`
- `VITE_THEME_*` (opcionais)

Compatibilidade de flag interna:

- Canonical: `VITE_ENABLE_INTERNAL_MENTOR_SURFACE`
- Alias legado ainda aceito: `VITE_ENABLE_INTERNAL_MENTOR_DEMO`

## Portabilidade e branding

- Ajuste `public/branding/*` para os ativos do cliente destino.
- Mantenha `VITE_ENABLE_DEMO_MODE=false` em ambientes de cliente.
- Em deploy sob subpath, alinhe `VITE_APP_BASE_PATH` com a configuração do host.
