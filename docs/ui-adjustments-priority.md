# UI Adjustments Priority

Data: 2026-03-13

## Objetivo

Priorizar os ajustes finais encontrados na auditoria visual consolidada, com foco em layout e clareza de leitura por tela.

## High

Nenhum ajuste `High` foi identificado como bloqueador da validacao visual do conjunto.

## Medium

### Aluno

1. Atualizar o texto de spotlight da sidebar para refletir a arquitetura atual de navegacao.
Motivo:
o layout ja nao usa abas centrais, mas a copia ainda sugere esse modelo.

2. Revisar o comportamento de ajuda contextual em cenarios mobile/touch.
Motivo:
o popover atual foi desenhado com boa logica de hover em desktop, mas a descoberta e permanencia em toque ainda pedem criterio explicito.

3. Refinar a consistencia vertical entre as quatro visoes principais.
Motivo:
Radar, Linha do Tempo, Indicadores e Sua Jornada funcionam, mas ainda variam bastante em altura, ritmo e distribuicao de respiro.

### Mentor

4. Reavaliar a folga do canvas central em larguras desktop menores.
Motivo:
a estrutura de tres colunas sustenta bem a leitura, mas pode comprimir views densas como matriz e centro de comando.

### Admin

5. Reavaliar a folga do canvas central em larguras desktop menores.
Motivo:
o perfil Admin repete a logica de tres colunas com blocos largos e leitura institucional, o que reduz respiracao da area central em alguns cenarios.

## Low

### Login

1. Revisar futuramente se a coluna hero precisa de uma segunda camada visual leve ou se deve permanecer apenas como palco de marca.
Motivo:
o layout esta limpo e funcional, mas parte da largura esquerda fica propositalmente subutilizada.

2. Preservar o alinhamento fino do logo em qualquer rodada futura de branding.
Motivo:
essa tela ja passou por refinamento de posicao e contraste; novos ajustes pequenos podem reintroduzir ruido.

### Mentor

3. Controlar o peso visual das areas complementares em relacao ao miolo principal.
Motivo:
em algumas leituras, a rail direita se aproxima demais da importancia do conteudo central.

### Admin

4. Reavaliar o peso estrutural da sidebar com apenas uma visao principal.
Motivo:
a coluna esquerda esta formalmente correta, mas a quantidade de navegacao nela ainda e pequena frente ao espaco ocupado.

### Aluno

5. Refinar o ritmo visual da transicao entre visoes com mais e menos densidade.
Motivo:
as visoes estao corretas por funcao, mas ainda podem ganhar mais uniformidade de cadencia espacial.

## Ordem Recomendada de Execucao

1. Alinhar a copia estrutural do Aluno com a navegacao atual.
2. Revisar comportamento de ajuda contextual do Aluno para mobile/touch.
3. Ajustar densidade do canvas central de Mentor e Admin.
4. Fechar refinamentos leves de ritmo e polimento.

## Fechamento

O sistema visual esta estavel para validacao.
As proximas iteracoes devem ser de refinamento dirigido, e nao de reconstrucao estrutural.
