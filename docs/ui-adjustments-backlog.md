# UI Adjustments Backlog

Source CSV: `C:\Users\dmene\Downloads\UI-Adjustments-Backlog - Backlog.csv`

| ID | Status | Page/File | Adjustment | Priority | Acceptance | Notes |
|----|--------|-----------|------------|----------|------------|-------|
| ADJ-001 | done | frontend/src/pages/LoginPage.tsx | Hide `ROLE_PRESETS` from Login page, maintaining only the credentials input. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-002 | done | frontend/src/pages/LoginPage.tsx | Apply Brazilian Portuguese accentuation to all labels. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-003 | done | frontend/src/pages/LoginPage.tsx | Remove label `Entrar em Plataforma de Mentoria`. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-004 | done | frontend/src/pages/LoginPage.tsx | Remove label `Use as credenciais do ambiente configurado para acessar as superficies protegidas publicadas.` | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-005 | done | frontend/src/pages/LoginPage.tsx | Remove label `As credenciais deste ambiente sao geridas fora da interface. Nenhum usuario ou senha de demonstracao e exposto ao cliente.` | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-006 | done | frontend/src/pages/LoginPage.tsx | Exchange yellow label `Acompanhamento com visao operacional` to client's product name. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-007 | done | frontend/src/pages/LoginPage.tsx | Return to use `env` to load data for Login page. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-008 | done | frontend/src/pages/LoginPage.tsx | Elaborate an env file for each different Client. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-009 | done | frontend/src/pages/LoginPage.tsx | Fill this new env file with all Client App Front end data: Icons, Logo, Colors related; and also all Client Showable back and Data: Client Name, Product, etc... | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-010 | done | frontend/src/pages/LoginPage.tsx | With this new client env file, use it when loading front and back end (set this as a parameter = client_code). | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-011 | done | frontend/src/pages/LoginPage.tsx | Make mentor credentials login access the app main page instead of falling into `403 Acesso negado` when using `mentor@swaif.local` / `mentor123`. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Login |
| ADJ-012 | done | frontend/src/features/matrix/pages/MatrixPage.tsx | On the Matrix page, when logged in as a mentor, remove the section titled `Mentor | Matriz de Decisão` / `Renovações, resgates e prioridades da carteira` and its description text, keeping only the metrics row below. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Matrix |
| ADJ-013 | todo | frontend/src/features/matrix/pages/MatrixPage.tsx | Remove the actions block to release space on the Matrix page. | high |  | Client: Grupo Acelerador Medico \| Product: Todos \| Page: Matrix |
