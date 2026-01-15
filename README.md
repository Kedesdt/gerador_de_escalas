# Sistema de Escalas de Funcionários

Sistema completo de gerenciamento de escalas de trabalho desenvolvido em Flask e Python.

## Funcionalidades

### Painel Administrativo

- ✅ Cadastro e autenticação de administradores
- ✅ Gerenciamento completo de funcionários (CRUD)
- ✅ Cadastro de férias
- ✅ Calendário interativo com drag-and-drop
- ✅ Bloqueio de dias (ninguém pode folgar)
- ✅ Geração automática de escalas inteligente

### Regras de Escalas

- ✅ Ninguém folga em dias bloqueados
- ✅ Mínimo de 1 folga por semana
- ✅ Um fim de semana completo de folga por mês
- ✅ Respeita períodos de férias
- ✅ Considera preferências de folga dos funcionários

### Painel de Visualização

- ✅ Visualização pública das escalas
- ✅ Calendário mensal com status de cada funcionário
- ✅ Diferenciação visual entre trabalhando, folga e férias

## Instalação

### 1. Clone o repositório ou navegue até a pasta do projeto

```powershell
cd c:\Users\kdtorres\Documents\Programacao\controle_de_escalas
```

### 2. Crie um ambiente virtual Python

```powershell
python -m venv venv
```

### 3. Ative o ambiente virtual

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 5. Execute o aplicativo

```powershell
python app.py
```

### 6. Acesse o sistema

Abra o navegador e acesse: `http://127.0.0.1:5000`

## Primeiro Acesso

1. Na primeira vez, você será redirecionado para a página de cadastro
2. Crie sua conta de administrador
3. Faça login com suas credenciais
4. Comece adicionando funcionários

## Estrutura do Banco de Dados

### Tabela: Admin

- id (PK)
- nome
- email
- senha_hash

### Tabela: Funcionario

- id (PK)
- nome
- preferencia_folga (dia da semana preferencial)
- horario_inicio
- horario_fim
- admin_id (FK)

### Tabela: Folga

- id (PK)
- funcionario_id (FK)
- data

### Tabela: Ferias

- id (PK)
- funcionario_id (FK)
- data_inicio
- data_fim

### Tabela: DiaBloqueado

- id (PK)
- admin_id (FK)
- data

## Como Usar

### Gerenciar Funcionários

1. Acesse "Funcionários" no menu
2. Clique em "Novo Funcionário"
3. Preencha os dados e salve

### Cadastrar Férias

1. Acesse "Férias" no menu
2. Clique em "Cadastrar Férias"
3. Selecione o funcionário e o período

### Gerenciar Escalas no Calendário

1. Acesse "Calendário" no menu
2. Arraste os nomes dos funcionários para os dias desejados
3. Clique no ícone de cadeado para bloquear/desbloquear dias
4. Clique em "Gerar Sugestão de Escala" para criar automaticamente

### Visualizar Escalas

1. Clique em "Visualização Pública"
2. Veja o calendário com todos os funcionários
3. Verde = Trabalhando, Azul = Folga, Amarelo = Férias

## Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Banco de Dados**: SQLite + SQLAlchemy
- **Autenticação**: Flask-Login
- **Frontend**: Bootstrap 5 + Bootstrap Icons
- **JavaScript**: Vanilla JS (Drag and Drop API)

## Segurança

- Senhas criptografadas com Werkzeug
- Sessões seguras com Flask-Login
- Proteção CSRF automática do Flask
- Validação de permissões em todas as rotas

## Personalização

### Alterar a chave secreta

Edite o arquivo `app.py` e altere a linha:

```python
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-mude-em-producao'
```

### Alterar porta do servidor

No final do arquivo `app.py`:

```python
app.run(debug=True, port=5000)  # Altere 5000 para a porta desejada
```

## Licença

Este projeto é de código aberto e pode ser usado livremente.

## Suporte

Para dúvidas ou problemas, consulte a documentação do Flask em: https://flask.palletsprojects.com/
