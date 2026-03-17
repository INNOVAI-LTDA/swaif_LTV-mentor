# UI Visual Audit

Data: 2026-03-13

## Escopo

Auditoria visual consolidada das telas:
- Login
- Mentor
- Aluno
- Admin

Foco desta etapa:
- layout
- hierarquia visual
- distribuicao espacial
- consistencia entre shells
- clareza de leitura por perfil

Observacao:
esta auditoria considera o estado atual da implementacao, incluindo os refinamentos recentes feitos na tela do Aluno apos a Etapa 4.

## Leitura Consolidada

Conclusao geral:
- a linguagem visual esta consistente entre os quatro perfis
- o branding premium escuro com acento dourado se manteve coeso
- a separacao de leitura por papel ficou clara
- o sistema de shell lateral + cabecalho + superficie central funciona bem para Mentor, Aluno e Admin

Ponto mais forte do conjunto:
- cada perfil le com um ritmo proprio sem perder a identidade da marca

Ponto principal a monitorar:
- a densidade da composicao de tres colunas ainda exige cuidado em Mentor e Admin

## Analise Por Tela

### 1. Login

Estrutura atual de layout:
- hero visual na coluna esquerda
- painel de acesso na coluna direita
- hierarquia clara: branding, titulo, selecao de perfil, resumo do destino, formulario

O que funciona bem:
- a composicao em duas colunas cria boa primeira impressao
- o painel de login tem hierarquia limpa e bem compartimentada
- a dimerizacao do fundo reduziu o conflito entre arte e logo
- a selecao por cards organiza bem a decisao antes do CTA principal

Leitura de layout:
- o painel da direita e o centro real da acao, com fluxo visual linear e facil de escanear
- o hero da esquerda cumpre papel de assinatura visual e nao compete mais com o formulario

Findings:
- `Low`: a coluna esquerda hoje opera quase como palco de marca, mas sem segunda camada de informacao; isso e aceitavel, porem deixa parte da largura desktop menos aproveitada
- `Low`: a composicao depende bastante da escala correta do logo; qualquer novo ajuste fino precisara preservar o alinhamento atual para nao reabrir ruido visual

### 2. Mentor

Estrutura atual de layout:
- sidebar esquerda com navegacao principal
- miolo central com cabecalho, KPIs e view analitica
- rail direita com area complementar

O que funciona bem:
- a estrutura de tres colunas sustenta bem a leitura executiva
- os KPIs no topo ajudam a contextualizar antes do mergulho no conteudo
- a navegacao principal entre Matriz, Centro de Comando e Radar ficou coerente
- a rail direita funciona como suporte sem confundir a visao principal

Leitura de layout:
- o Mentor tem a melhor organizacao para leitura de carteira e decisao
- a composicao privilegia clareza analitica e sensacao de controle operacional

Findings:
- `Medium`: em larguras desktop menores, a combinacao sidebar + rail + canvas analitico reduz a respiracao da area central e pode apertar tabelas, boards e blocos mais densos
- `Low`: as areas complementares permanecem visualmente fortes, o que por vezes disputa atencao com a visao principal em telas mais cheias

### 3. Aluno

Estrutura atual de layout:
- sidebar esquerda com quatro visoes principais: Radar, Linha do Tempo, Indicadores e Sua Jornada
- miolo central variando por visao
- rail direita recolhida por padrao e aberta sob demanda nas Areas de Apoio

O que funciona bem:
- a tela finalmente assumiu postura de aluno autenticado, e nao de operador
- a retirada das abas centrais liberou mais largura para cada visao
- a abertura condicional da rail direita melhorou muito a concentracao no conteudo principal
- a separacao entre visoes ficou clara e bem orientada por intencao de leitura
- a visao `Sua Jornada` sem grafico reforca corretamente o papel contextual dela

Leitura de layout:
- Radar funciona como entrada principal
- Linha do Tempo e Indicadores agora sustentam leituras proprias, com grafico e secoes associadas
- Sua Jornada ocupa bem o papel de leitura textual e contextual

Findings:
- `Medium`: o bloco de spotlight da sidebar ainda menciona "abas complementares", enquanto a navegacao principal ja foi migrada para a propria sidebar; ha desalinhamento entre a copia e o layout atual
- `Medium`: os popovers de ajuda funcionam bem em desktop, mas a permanencia baseada em hover pode exigir atencao futura em contexto mobile/touch
- `Low`: como cada visao tem altura e densidade distintas, a tela muda bastante de ritmo ao alternar entre modos; isso nao quebra a leitura, mas ainda pede refinamento fino de consistencia vertical

### 4. Admin

Estrutura atual de layout:
- sidebar esquerda com leitura principal institucional
- miolo central com cabecalho, metricas e blocos estrategicos
- rail direita com areas de supervisao

O que funciona bem:
- a composicao transmite institucionalidade e controle
- a area central comunica melhor portfolio, base e governanca do que os demais perfis
- a hierarquia do cabecalho e dos resumos ajuda a leitura executiva
- a rail direita complementa bem a ideia de supervisao

Leitura de layout:
- o Admin se diferencia corretamente do Mentor por parecer menos tatico e mais orquestrador
- a estrutura sustenta bem uma narrativa de "visao da operacao"

Findings:
- `Medium`: a estrutura fixa de tres colunas no Admin carrega densidade semelhante a do Mentor, mas com blocos ainda mais institucionais; em larguras menores, o canvas central pode perder folga visual
- `Low`: a sidebar possui apenas uma visao principal, o que enfraquece um pouco a proporcao entre peso estrutural da coluna esquerda e quantidade real de navegacao nela

## Consistencia Entre Perfis

O que esta consistente:
- paleta
- materiais visuais
- bordas, sombras e superficies
- cabecalho principal com titulo e descricao
- padrao de metricas no topo quando aplicavel

O que ainda merece alinhamento:
- criterio de abertura da rail direita varia entre perfis e ainda nao esta uniformizado
- densidade dos shells de Mentor e Admin continua mais pesada que a do Aluno, o que e correto por papel, mas exige controle para nao gerar saturacao visual
- textos auxiliares precisam acompanhar as mudancas recentes de arquitetura de navegacao, especialmente no Aluno

## Status da Auditoria

- `High`: nenhum bloqueio visual estrutural encontrado para validacao do conjunto
- `Medium`: existem ajustes importantes de espacamento, densidade e consistencia de copia
- `Low`: restam refinamentos de polimento e alinhamento fino

## Recomendacao Final

O conjunto esta pronto para uma rodada final de refinamento orientada por prioridade escrita, sem necessidade de refatoracao ampla de layout.
