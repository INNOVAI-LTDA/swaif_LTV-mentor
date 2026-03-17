# Caso Mentoria Acelerador Médico

- Aproveitar a DEMO SWAIF-LTV de Mentoria e transformá-la em um MVP apresentável e navegável ao cliente
- A hierarquia segue essa estrutura: 
-- Cliente(Empresa)->Produto(Mentoria)->Mentor->Aluno ;
-- Produto(Mentoria)->Pilar->Métrica

## Features
- F1: Tela Inicial de login, colocando um plano de fundo algo da identidade visual do cliente. Formulário que captura usuário e senha.
- F2: Tipos de usuários: Mentor, Aluno e Admin
- F3: Tela do Mentor. Ela é dividida em 3 abas de visão, exibidas na seguinte ordem: Matriz de Decisão, Centro de Comando e Radar de Evolução. Além disso, ele pode acessar informações mais administrativas, como uma View de Produtos, outra de Alunos e uma área de usuário (cadastro e credenciais).
- F4: Tela do Aluno. Ela é uma tela simples porém apresenta uma visão principal do seu Radar de Evolução, seguido de uma linha do tempo de progresso e um painel com seus indicadores. Além disso, ele pode acessar informações mais administrativas, como uma View de Produtos, outra de Mentores e uma área de usuário (cadastro e credenciais).
- F5: Tela do Admin. A tela mais complexa, pois ela embarca tudo que o mentor e aluno enxerga, só que sob uma ótica mais administrativa ele é único que aplica as 4 operações CRUD (Create, Read, Update, Delete). Começando pela operação **Read**, ele possui as seguintes Abas: Cliente, Mentor, Aluno. Na aba cliente, 3 views: Produtos do Cliente, Mentores do Cliente, Alunos do Cliente. Na aba Mentor, 2 views: Produtos por Mentor, Alunos por Mentor. Na aba Aluno, 2 abas: Produtos por Aluno, Mentores por Aluno. Além disso, ele possui um menu onde pode realizar as outras 3 operações (**Create, Update, Delete**) para todos os objetos: Cliente, Produto, Pilar, Metrica, Mentor e Aluno. Quando o usuário seleciona por cadastrar (**Create**) um objeto, ele vai abrir um formulário estilo pop-up que variam os campos pelo tipo de objeto e seguem uma regra de negócio para garantir um cadastro relacionado corretamente. Outro detalhe é que existem duas formas de cadastro de um novo objeto: Individualizado e Por Lotes. No cadasto individualizado, o usuário apenas preenche os campos para apenas 1 registro. Já o Por Lotes permite o usuário inserir mais de 1 registro, através da importação de arquivos de dados estruturados: planilha excel, planilha google, csv, json e xml. A implicação é de que os campos vazios serão preenchidos com valores default (texto: "VAZIO", número: -99, data: 01/01/0001, opção: N/A). Cabe o usuário corrigir isso após a importação. Nas operações de **Update e Delete**, o usuário pode buscar o registro por Cliente(obrigatório para prosseguir com os outros), Produto, Mentor ou Aluno. Nos casos de Mentor ou Aluno é possível buscar por CPF ou pelo Nome (Dropdownlist). No caso do Cliente, a busca é pelo CNPJ ou pelo Nome (Dropdownlist). No caso do produto ainda é possível fazer uma busca interna por Pilar ou Métrica. Em ambas, a busca é apenas pelo Nome (Dropdownlist). Aqui ele já irá ver uma tabela contendo todos os produtos daquele cliente. Em todos os registros listados nessa tabela visualizada vai existir uma coluna chamada "Ações", contendo duas opções: Editar (icone de lápis) / Deletar (icone placa vermelha com X). Em quaisquer caso das operações CRUD, o usuário vai receber uma mensagem de Pop-Up pedindo uma confirmação da operação selecionada.
 
- F6: Tela de Cadastro. 
- F7: Aplicação de RBAC (*Role-based Access Control*): Aqui temos uma matriz que indica o que cada usuário pode fazer ou não em termos das operações CRUD. 
| Usuário | Acessibilidade | Descrição |
| :---: | :---: | :--- | 
| Aluno | R, U | U: Cadastro e Credenciais. |
| Mentor | C,R,U | C: Produtos, Pilares e Metricas. U: Pilares, Metricas, Cadastro e Credenciais |
| Admin  | C,R,U,D| Acesso e Controle Total. |

-F8: Aplicação de Identidade Visual na UI da solução. Combinar as imagens enviadas em cadastro (ícones, logos) para extração de cores e formas a aplicação. Deve se ter uma atenção redobrada para não afetar a usabilidade do usuário (usar contrastes, por exemplo). Podemos usar prints de materias digitais do cliente como exemplo/padrão a ser usado.

## Regras de negócio (BI)

- BI-1 (Premissa): Regra de Operações com dependência hierárquica. Devido a hierarquia de dados apresentada no início, as operações que manipulam dados (C e D) não podem ser feitas de qualquer jeito. Todas as telas que permitem realizar as operações vai conter um campo "Responsável:", mostrando o nome do usuário (login), sendo imutável e um campo "Justificativa" obrigatório a ser preenchido (apenas para Remoção e Atualização).
- BI-1.1: Fluxos de Cadastros (C). Seguindo BI-1, os possíveis fluxos de cadastros são:
	-- Cadastro Cliente {Nome, CNPJ, Id. Visual(img)}
	-- Cadastro Produto (Cliente) {Nome, Ícone(img), Xpto} <!-- Dependencia do Cliente para cadastrar -->
	-- Cadastro Pilar (Produto) {Nome, Descrição, Valor, Alvo, Ícone(img)} <!-- Dependencia do Produto para cadastrar -->	
	-- Cadastro Métrica (Pilar) {Nome, Descrição, Valor, Alvo, Ícone(img)} <!-- Dependencia do Pilar para cadastrar -->
	-- Cadastro Mentor (Produto) {Nome, CPF, Xpto} <!-- Dependencia do Produto para cadastrar -->
	-- Cadastro Aluno (Mentor) {Nome, CPF, Xpto} <!-- Dependencia do Mentor para cadastrar -->
	
- BI-1.2: Fluxos de Remoção (D). Seguindo BI-1, os possíveis fluxos de remoção são:
	| Objeto | Folha? | Filhos | Fluxo D |
	| :---: | :---: | :---: | :--- |
	| Aluno | S | | Aluno |
	| Metrica | S | | Metrica |
	| Mentor | N | Aluno | Aluno->Mentor |
	| Pilar | N | Metrica | Metrica->Pilar |
	| Produto | N | Mentor, Pilar | (Mentor, Pilar)->Produto |
	| Cliente | N | Produto | Produto->Cliente |
	
## Hierarquia de Visualizações

- Tela Inicial: Login (via URL)
	- Tela Aluno
		- Aba Radar de Evolução (principal)
		- Aba Produtos
		- Aba Mentores
		- Aba Usuário
			- Link "Meu cadastro"
				- Tela Cadastro de Usuário: Aluno { Nome, Tipo de usuário, Data Nascimento, CPF, Email, Telefone, Endereço, Origem, Produto, Mentor, Xpto }
			- Link "Credenciais"
				- Tela de Credenciais de Usuário: Aluno {Nome, usuário, senha(exibir "---")}
	- Tela Mentor
		- Aba Matriz de Decisão (principal)
		- Aba Centro de Comando
		- Aba Radar de Evolução 
		- Aba Produtos
		- Aba Alunos
		- Aba Usuário
			- Link "Meu cadastro"
				- Tela Cadastro de Usuário: Mentor { Nome, Tipo de usuário, Data Nascimento, CPF, Email, Telefone, Endereço, Mentor, Xpto }
			- Link "Credenciais"
				- Tela de Credenciais de Usuário: Mentor {Nome, usuário, senha(exibir "---")}
	- Tela Admin
		- Aba Cliente (principal)
		- Aba Produtos
		- Aba Mentores
		- Aba Alunos
		- Aba Operações
		- Aba Usuário
			- Link "Meu cadastro"
				- Tela Cadastro de Usuário: Admin { Nome, Tipo de usuário, Data Nascimento, CPF, Email, Telefone, Endereço}
			- Link "Credenciais"
				- Tela de Credenciais de Usuário: Admin {Nome, usuário, senha(exibir "---")}