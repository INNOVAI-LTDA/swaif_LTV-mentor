# MVP Bootstrap - Guia Copiar e Colar (Windows)

Este guia prepara o ambiente para voce executar o bootstrap com o minimo de decisao manual.

## 1) Pre-requisitos (copiar e colar)

Abra o PowerShell e rode:

```powershell
python --version
node --version
npm --version
```

Resultado esperado:
- Python 3.10+ (obrigatorio)
- Node 18+ e npm (obrigatorios apenas para subir frontend)

Se algum comando falhar, instale a dependencia e rode novamente.

## 2) Entrar na pasta do projeto (copiar e colar)

```powershell
Set-Location "C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria"
```

## 3) Definir pasta do frontend (opcional)

Use esta etapa se voce quiser subir frontend junto.
O bootstrap procura `package.json` com script `dev`; se nao encontrar frontend valido, ele sobe apenas backend.

Use um dos blocos abaixo.

### 3.1) Definir so para a sessao atual (recomendado para pre-demo)

```powershell
$env:FRONTEND_DIR = "C:\caminho\para\seu\frontend"
```

### 3.2) Definir persistente no Windows (abre novo terminal depois)

```powershell
setx FRONTEND_DIR "C:\caminho\para\seu\frontend"
```

Opcional: se quiser forcar um comando custom de start:

```powershell
$env:FRONTEND_CMD = "npm run dev"
```

## 4) Inspecionar portas antes de subir (copiar e colar)

```powershell
python scripts\mvp_bootstrap.py --ports
```

Esperado: backend 8000 e frontend 5173 livres.

## 5) Subir servicos (copiar e colar)

### 5.1) Backend + Frontend

```powershell
scripts\mvp_bootstrap.bat
```

### 5.2) Somente backend

```powershell
scripts\mvp_bootstrap.bat --backend-only
```

### 5.3) Somente frontend (quando backend ja estiver no ar)

```powershell
scripts\mvp_bootstrap.bat --frontend-only
```

## 6) Modo seguro (nao matar processos automaticamente)

Se preferir nao encerrar processo ocupando porta:

```powershell
scripts\mvp_bootstrap.bat --no-kill
```

## 7) Como encerrar

Com o bootstrap em execucao:
- Pressione `Ctrl + C`

## 8) Logs (copiar e colar)

```powershell
Get-Content .logs\mvp-bootstrap\backend.log -Tail 80
Get-Content .logs\mvp-bootstrap\frontend.log -Tail 80
```

## 9) Solucao rapida de problemas (copiar e colar)

### 9.1) Erro: comando do frontend nao detectado

```powershell
$env:FRONTEND_DIR = "C:\caminho\para\seu\frontend"
scripts\mvp_bootstrap.bat
```

### 9.2) Erro: porta ocupada e falha ao encerrar

1. Feche terminais/IDEs que possam estar rodando servidor.
2. Abra PowerShell como Administrador.
3. Rode novamente:

```powershell
Set-Location "C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria"
scripts\mvp_bootstrap.bat
```

### 9.3) Validar backend no navegador

Abra:
- `http://127.0.0.1:8000/health`

## 10) Fluxo minimo para demo (copiar e colar)

```powershell
Set-Location "C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria"
$env:FRONTEND_DIR = "C:\caminho\para\seu\frontend"
python scripts\mvp_bootstrap.py --ports
scripts\mvp_bootstrap.bat
```

Se tudo subir:
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`
