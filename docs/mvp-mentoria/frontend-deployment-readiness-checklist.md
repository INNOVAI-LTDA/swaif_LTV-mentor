# Frontend Deployment Readiness Checklist

Date: 2026-03-19

## Objetivo

Transformar o frontend atual de ambiente de demo validada para uma entrega segura, configuravel e apresentavel ao cliente.

Este documento deixa de ser apenas uma checklist estatica e passa a ser o workflow oficial de execucao da release de frontend. Cada bloco precisa registrar owner, status, evidencia objetiva e bloqueador antes da liberacao para homologacao ou cliente.

## Como usar este workflow

- Nao marcar um item sem evidencia objetiva anexada no tracker de release.
- Cada bloco deve terminar com build, testes e validacao manual do fluxo principal daquele bloco.
- Qualquer comportamento exclusivo de demo deve estar removido ou protegido por flag explicita de ambiente nao produtivo.
- Nenhum bloqueador desta lista pode permanecer aberto no momento do deploy.
- Preencher os campos de controle abaixo antes de iniciar homologacao.

## Controle da release

| Campo | Valor |
| ---- | ----- |
| Release ID | `local-accmed-20260320` |
| Ambiente alvo | `local (baseline para staging)` |
| Frontend origin alvo | `http://127.0.0.1:4173` |
| Base path alvo | `/accmed/` |
| Backend URL alvo | `http://127.0.0.1:8000` |
| APP_ENV backend | `local` |
| CORS_ALLOW_ORIGINS backend | `http://127.0.0.1:4173` |
| Responsavel operacional | `dmene` |
| Responsavel tecnico | `dmene` |

Nota operacional atual:

- O valor `/accmed/` acima continua sendo a baseline local registrada nesta checklist.
- Para o deploy Vercel preparado no Batch A, o contrato hospedado atual e `VITE_APP_BASE_PATH=/`.

## Status permitidos

- `pending`: ainda nao iniciado
- `in_progress`: em execucao
- `blocked`: nao pode continuar sem resolver bloqueador
- `done`: concluido com evidencia objetiva revisada
- `waived`: fora de escopo desta release com aprovacao explicita

## Registro por bloco

Preencher o status de cada bloco no tracker e repetir abaixo o link ou local da evidencia principal.

| Bloco | Owner | Status | Evidencia principal | Bloqueador atual | Data |
| ---- | ----- | ------ | ------------------- | ---------------- | ---- |
| 1. Autenticacao e seguranca de acesso | `dmene` | `done` | `EV-002, EV-005, EV-010` | `nenhum` | `2026-03-20` |
| 2. Roteamento e hospedagem | `dmene` | `in_progress` | `EV-010, EV-011` | `Rewrite versionada; falta validar refresh profundo e navegacao protegida no host real` | `2026-03-20` |
| 3. Configuracao de ambiente e integracao com API | `dmene` | `in_progress` | `EV-010, EV-011` | `O pacote local existe, mas browser-origin, CORS real e ausencia de localhost no ambiente remoto ainda nao foram validados` | `2026-03-20` |
| 4. Branding e conteudo do cliente | `dmene` | `in_progress` | `EV-005, EV-010, EV-011` | `Os valores baseline atuais foram fixados, mas a revisao final dos ativos publicados ainda falta` | `2026-03-20` |
| 5. Limpeza de comportamentos de demo | `dmene` | `in_progress` | `EV-005, EV-011` | `O scan amplo ainda encontra referencias internas em docs, testes e codigo gated; a superficie publicada agora isola mentor-demo, mas a decisao final sobre produto mentor continua pendente` | `2026-03-20` |
| 6. Observabilidade basica e falha controlada | `dmene` | `in_progress` | `EV-003, EV-008, EV-010` | `Ainda falta a validacao manual em browser para backend indisponivel e expiracao de sessao em ambiente hospedado` | `2026-03-20` |
| 7. Qualidade de release | `dmene` | `in_progress` | `EV-001, EV-002, EV-003, EV-010` | `Build, testes e validacao local estao prontos, mas ainda falta smoke hospedado em browser` | `2026-03-20` |
| 8. Documentacao de deploy | `dmene` | `in_progress` | `EV-008, EV-010` | `Os artefatos estao prontos, mas faltam os parametros reais do staging e a revisao pelo operador final` | `2026-03-20` |

## Gate de saida

O frontend so pode ser considerado pronto para deploy quando:

- [x] nao houver login preview ativo em ambiente cliente
- [x] nao houver credenciais hardcoded expostas na interface
- [x] rotas protegidas exigirem autenticacao e papel compativel
- [x] configuracao de API e base path estiverem externalizadas
- [ ] branding e copy estiverem alinhados ao cliente alvo
- [x] build e testes estiverem verdes
- [ ] validacao manual do fluxo principal estiver aprovada

## Bloco 1 - Autenticacao e seguranca de acesso

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `done` | `EV-002, EV-005, EV-010` | `nenhum` | `dmene` |

- [ ] Remover da UI de login qualquer credencial hardcoded de demo.
- [ ] Remover o fluxo de `loginPreview` do bundle de cliente ou proteger por flag de ambiente nao produtivo.
- [ ] Remover armazenamento de sessao preview em `localStorage`.
- [ ] Garantir que a sessao dependa apenas do backend real em ambiente cliente.
- [ ] Criar guarda de rota para areas autenticadas.
- [ ] Criar guarda de papel para rotas administrativas.
- [ ] Impedir montagem de paginas protegidas sem sessao valida.
- [ ] Impedir que hooks de dados administrativos executem antes da validacao de autenticacao e role.
- [ ] Exibir fallback claro para usuario nao autorizado sem disparar chamadas desnecessarias.
- [ ] Validar logout e expiracao de token em todas as areas protegidas.

Leitura local atual do bloco:

- O comportamento preview permanece apenas para ambiente local/demo e e ignorado ou limpo em deploy de cliente.
- As evidencias desta fase vieram de testes automatizados e do pacote local `EV-010`; a repeticao em browser hospedado fica para o staging.

### Evidencias minimas do bloco

- [x] Login sem preview funciona com backend real.
- [x] Usuario sem sessao nao acessa `/app/*`.
- [x] Usuario sem role `admin` nao acessa a superficie administrativa.
- [x] Nenhum texto da UI expoe `admin@swaif.local`, `mentor@swaif.local`, `admin123` ou equivalentes.

## Bloco 2 - Roteamento e hospedagem

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-010` | `Falta a validacao no host real com rewrite e refresh profundo em browser` | `dmene` |

- [ ] Definir estrategia de deploy do SPA: raiz do dominio ou subpath.
- [ ] Introduzir `basename` configuravel no roteador para suportar subpath de cliente.
- [ ] Eliminar dependencias de caminhos absolutos fixos que assumem deploy em `/`.
- [ ] Ajustar links internos para respeitar o base path configurado.
- [ ] Ajustar carregamento de assets de branding para nao depender de `/branding/...` fixo.
- [ ] Confirmar no host a regra de rewrite para SPA em refresh direto de rota (rewrite ja versionada em `frontend/vercel.json`).
- [ ] Validar acesso direto por URL em `login`, `admin`, `centro`, `radar`, `aluno` e `matriz`.

### Evidencias minimas do bloco

- [ ] Build publicado em ambiente de teste responde corretamente em refresh de rota profunda.
- [ ] Assets carregam corretamente no host final.
- [ ] Navegacao continua funcional quando o app roda sob o base path definido.

### Registro de validacao de staging

| Verificacao | Resultado | Evidencia | Observacao |
| ---------- | --------- | --------- | ---------- |
| Host publica o app no origin correto | `pendente` | `preencher` | `Contrato Vercel atual usa /; falta validar no host real` |
| Base path configurado igual no build e no host | `parcial` | `EV-011` | `Build local validou /; falta validacao no host real` |
| Refresh em rota profunda reescreve para `index.html` | `pendente` | `preencher` | `Rewrite esta versionada; falta validar no host remoto` |
| Assets de branding carregam no base path publicado | `parcial` | `EV-011` | `Assets servidos localmente sob /accmed/assets/; falta o host remoto` |
| Navegacao protegida funciona sob o host real | `pendente` | `preencher` | `Falta browser real em staging` |
| Dominio customizado responde com TLS valido | `pendente` | `preencher` | `Falta conectar e validar o dominio final no host remoto` |
| Apex redireciona para `www` sem loop e preserva path/query | `pendente` | `preencher` | `Politica canonica ainda precisa ser validada no host remoto` |
| Politica de trailing slash fica estavel no host real | `pendente` | `preencher` | `Falta validar `/login` e `/login/` no dominio canonico` |

## Bloco 3 - Configuracao de ambiente e integracao com API

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-010` | `Contrato VITE_API_BASE_URL ja exige valor em client; falta validar CORS real, browser-origin e bundle publicado fora do loopback local` | `dmene` |

- [ ] Confirmar `VITE_API_BASE_URL` obrigatorio em ambiente hospedado (ja aplicado no contrato de build `client`).
- [ ] Evitar fallback silencioso para `http://127.0.0.1:8000` em build de cliente (permitido apenas em `local`).
- [ ] Documentar todos os env vars necessarios para deploy.
- [ ] Criar arquivo de exemplo de ambiente voltado ao cliente ou homologacao.
- [ ] Validar timeouts HTTP para rede real do cliente.
- [ ] Confirmar compatibilidade de CORS entre frontend publicado e backend alvo.
- [ ] Confirmar comportamento de erro para `401`, `403`, `404`, `409` e `422` em ambiente integrado.
- [ ] Validar que nenhuma chamada de API aponta para localhost apos build.

### Evidencias minimas do bloco

- [ ] Build falha ou alerta explicitamente quando `VITE_API_BASE_URL` obrigatorio estiver ausente.
- [ ] Smoke test integrado roda com URL real do backend.
- [ ] Inspecao manual do bundle ou do comportamento em runtime confirma ausencia de dependencia operacional em localhost.

### Registro de integracao com backend

| Verificacao | Resultado | Evidencia | Observacao |
| ---------- | --------- | --------- | ---------- |
| `VITE_API_BASE_URL` aponta para o backend alvo | `parcial` | `EV-011` | `O build local aponta para http://127.0.0.1:8000 por definicao desta fase; falta o backend remoto` |
| `APP_ENV` backend esta explicito | `done` | `EV-010` | `Validado localmente com APP_ENV=local e runtime summary registrado` |
| `CORS_ALLOW_ORIGINS` inclui apenas a origin real do frontend | `pendente` | `preencher` | `Falta a origin real do staging` |
| Resposta `401` limpa sessao e redireciona como esperado | `parcial` | `EV-010` | `401 local validado na camada de API; falta validacao integrada em browser` |
| Resposta `403` exibe negacao de acesso controlada | `parcial` | `EV-010` | `403 local validado na API; falta validacao integrada em browser` |
| Nenhuma request publicada aponta para localhost | `pendente` | `preencher` | `O build desta fase usa loopback local de proposito` |

## Bloco 4 - Branding e conteudo do cliente

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-005, EV-010, EV-011` | `O baseline atual usa Acelerador Médico (AccMed) + Gamma, mas a revisao final dos ativos publicados ainda falta` | `dmene` |

- [ ] Externalizar nome do cliente, titulo do produto e metadados principais.
- [ ] Substituir logos e icones de demo pelos ativos do cliente.
- [ ] Revisar `title`, `meta` e textos de entrada do app.
- [ ] Remover narrativas explicitamente comerciais de demo quando nao fizerem parte do produto final.
- [ ] Revisar copy de login, hub, mentor, aluno e admin para linguagem de entrega real.
- [ ] Remover referencias visiveis a `Acelerador Medico` quando o deploy for para outro cliente.
- [ ] Validar acessibilidade minima de imagens, rotulos e contraste apos troca de branding.

### Evidencias minimas do bloco

- [ ] Login reflete a marca correta do cliente.
- [ ] Topbar, shells e titulos internos refletem o nome correto do produto.
- [ ] Nenhum texto residual de demo aparece em busca por strings de branding antigo.

## Bloco 5 - Limpeza de comportamentos de demo

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-005, EV-011` | `O scan amplo ainda retorna referencias internas e a decisao final sobre uma futura superficie mentor segue em aberto, mas o caminho publicado atual ja isola mentor-demo` | `dmene` |

- [ ] Mapear todos os fluxos que existem apenas para apresentacao comercial.
- [ ] Separar claramente o que permanece como fixture de homologacao e o que sai do produto.
- [ ] Remover mensagens que indiquem explicitamente `demo`, `preview`, `carga demo` ou similares do frontend cliente.
- [ ] Revisar a tela do mentor para eliminar narrativa de demonstracao isolada, se nao fizer parte do escopo final.
- [ ] Revisar a tela do aluno para eliminar mapeamentos fixos por email demo.
- [ ] Revisar a tela administrativa para eliminar instrucoes de uso de credenciais locais.
- [ ] Confirmar se a carga demo do mentor deve existir apenas em ambiente comercial interno e nunca em cliente.
- [x] Isolar a superficie mentor-demo da experiencia publicada, mantendo-a disponivel apenas por flag local explicita.

### Evidencias minimas do bloco

- [ ] Busca textual no frontend nao retorna strings operacionais de demo indevidas.
- [ ] Sessao de aluno depende de identidade real ou fluxo explicitamente homologado.
- [ ] Admin nao orienta uso de usuario ou senha locais de desenvolvimento.

### Receita de busca de residuos

Executar e anexar a saida final:

```powershell
rg -n "admin@swaif\\.local|mentor@swaif\\.local|admin123|mentor123|preview|demo|Acelerador Medico|127\\.0\\.0\\.1|localhost" frontend
```

Resultado local atual:

- Evidencia anexada em `EV-005`.
- O scan amplo ainda encontra referencias intencionais em testes, docs, configuracao local do Vite e codigo explicitamente gated para uso interno.
- A superficie cliente validada em Story `1.2` continua limpa para as credenciais hardcoded e branding antigo; a superficie mentor-demo agora tambem ficou fora do caminho publicado por default. Repetir o scan final na superficie publicada em `4-2`.

## Bloco 6 - Observabilidade basica e falha controlada

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-003, EV-008, EV-010` | `Falta exercitar indisponibilidade do backend e expiracao de sessao em browser` | `dmene` |

- [ ] Garantir mensagens de erro compreensiveis para falha de rede e autorizacao.
- [ ] Definir comportamento visivel para indisponibilidade temporaria do backend.
- [ ] Confirmar que o app nao entra em loop de refresh ou chamada repetitiva quando a API falha.
- [ ] Validar que erros de autorizacao limpam sessao e redirecionam corretamente quando aplicavel.
- [ ] Registrar minimamente eventos de falha de integracao, se houver estrategia de observabilidade do projeto.

### Evidencias minimas do bloco

- [ ] Teste manual de backend indisponivel nao quebra a navegacao inteira.
- [ ] Teste manual de token invalido encerra a sessao de forma previsivel.

## Bloco 7 - Qualidade de release

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-001, EV-002, EV-003, EV-010` | `Falta smoke integrado hospedado e revisao visual em browser` | `dmene` |

- [ ] Executar `npm run build`.
- [ ] Executar `npm run test`.
- [ ] Validar manualmente a navegacao principal em ambiente integrado.
- [ ] Validar login, logout e redirecionamento por role.
- [ ] Validar pelo menos um fluxo administrativo principal.
- [ ] Validar pelo menos um fluxo mentor principal.
- [ ] Validar pelo menos um fluxo aluno principal, se este perfil fizer parte do escopo real de entrega.
- [ ] Confirmar ausencia de regressao visual relevante apos troca de branding e ajustes de deploy.

### Evidencias minimas do bloco

- [x] Build verde anexado ao registro da entrega.
- [x] Suite de testes verde anexada ao registro da entrega.
- [ ] Checklist manual de navegacao preenchido.

## Bloco 8 - Documentacao de deploy

### Controle do bloco

| Owner | Status | Evidencia | Bloqueador | Aprovado por |
| ---- | ------ | --------- | ---------- | ------------ |
| `dmene` | `in_progress` | `EV-008, EV-010` | `Faltam os parametros reais do staging e a revisao do operador final` | `dmene` |

- [ ] Atualizar `frontend/README.md` com instrucoes de deploy, nao apenas setup local.
- [ ] Documentar env vars obrigatorios.
- [ ] Documentar estrategia de base path e rewrite do SPA.
- [ ] Documentar dependencia esperada do backend e origem permitida.
- [ ] Documentar quais comportamentos sao exclusivos de dev e homologacao.
- [ ] Documentar processo de troca de branding por cliente.
- [ ] Documentar smoke test pos-deploy.

### Evidencias minimas do bloco

- [ ] README revisado por quem fara o deploy.
- [ ] Time consegue subir o frontend em homologacao sem depender de conhecimento tacito.
- [ ] Contrato Vercel atual (`frontend` como root e `VITE_APP_BASE_PATH=/`) esta claro e nao conflita com exemplos locais em subpath.

## Registro de staging integrado

| Passo | Resultado | Evidencia | Bloqueador |
| ---- | --------- | --------- | ---------- |
| Frontend buildado com `VITE_DEPLOY_TARGET=client` | `pendente` | `preencher` | `nenhum` |
| Frontend publicado no host alvo | `pendente` | `preencher` | `nenhum` |
| Backend iniciado com `APP_ENV` e `CORS_ALLOW_ORIGINS` explicitos | `pendente` | `preencher` | `nenhum` |
| Dominio customizado publicado com host canonico `www` | `pendente` | `preencher` | `nenhum` |
| Apex redireciona para `www` no host publicado | `pendente` | `preencher` | `nenhum` |
| Rewrite de SPA validado em refresh profundo | `pendente` | `preencher` | `nenhum` |
| Base path validado no host real | `pendente` | `preencher` | `nenhum` |
| Login admin integrado validado | `pendente` | `preencher` | `nenhum` |
| Login mentor integrado validado | `pendente` | `preencher` | `nenhum` |
| Fluxo aluno validado ou dispensado formalmente | `pendente` | `preencher` | `nenhum` |
| Logout, expiracao e `403` validados | `pendente` | `preencher` | `nenhum` |
| Nenhuma request aponta para localhost | `pendente` | `preencher` | `nenhum` |
| Headers basicos de seguranca presentes no deploy | `pendente` | `preencher` | `nenhum` |

## Busca de residuos antes do deploy

Executar busca textual final e zerar residuos indevidos:

- [ ] `admin@swaif.local`
- [ ] `mentor@swaif.local`
- [ ] `admin123`
- [ ] `mentor123`
- [ ] `preview`
- [ ] `demo`
- [ ] `Acelerador Medico`
- [ ] `127.0.0.1`
- [ ] `localhost`

## Prioridade recomendada

1. Autenticacao e seguranca de acesso
2. Roteamento e hospedagem
3. Configuracao de ambiente e API
4. Branding e conteudo do cliente
5. Limpeza de demo
6. Qualidade de release
7. Documentacao de deploy

## Registro final de pronto

- [ ] Bloqueadores resolvidos
- [ ] Ajustes aprovados em homologacao
- [ ] Cliente correto configurado
- [ ] Deploy frontend executado
- [ ] Smoke pos-deploy aprovado
- [ ] Evidencias anexadas ao tracker de release
