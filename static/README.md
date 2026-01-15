# Estrutura de Arquivos Estáticos

Este documento descreve a organização dos arquivos CSS e JavaScript do sistema.

## Estrutura de Diretórios

```
static/
├── css/
│   ├── base.css                  # Estilos globais do sistema
│   ├── admin-calendario.css      # Estilos do calendário administrativo
│   └── visualizacao.css          # Estilos da visualização pública
└── js/
    └── admin-calendario.js       # JavaScript do calendário administrativo
```

## Descrição dos Arquivos

### CSS

#### base.css

- **Propósito**: Estilos comuns a todas as páginas
- **Conteúdo**: Layout flex do body, estilos do navbar
- **Usado em**: templates/base.html

#### admin-calendario.css

- **Propósito**: Estilos específicos do calendário administrativo
- **Conteúdo**:
  - Estilos da tabela do calendário
  - Slots de turnos e folgas (drag-and-drop)
  - Badges de funcionários
  - Estados visuais (drag-over, today, weekend, blocked-day)
- **Usado em**: templates/admin/calendario.html

#### visualizacao.css

- **Propósito**: Estilos da visualização pública
- **Conteúdo**:
  - Tabela do calendário público
  - Badges de status (working, vacation, off)
  - Legenda
- **Usado em**: templates/visualizacao.html

### JavaScript

#### admin-calendario.js

- **Propósito**: Funcionalidades interativas do calendário administrativo
- **Funções principais**:
  - `dragFunc()`, `dropTurno()`, `dropFolga()` - Drag and drop
  - `adicionarEscala()`, `removerEscala()` - Gestão de escalas via API
  - `adicionarFolga()`, `removerFolga()` - Gestão de folgas via API
  - `toggleBloqueio()` - Bloquear/desbloquear dias
  - `gerarEscala()` - Gerar sugestão automática de escala
  - `resolverAlerta()` - Marcar alertas como resolvidos
- **Usado em**: templates/admin/calendario.html

## Como Adicionar Novos Estilos/Scripts

### Para adicionar CSS a uma página específica:

1. Crie um arquivo em `static/css/nome-do-arquivo.css`
2. No template, adicione no bloco extra_css:

```html
{% block extra_css %}
<link
  rel="stylesheet"
  href="{{ url_for('static', filename='css/nome-do-arquivo.css') }}"
/>
{% endblock %}
```

### Para adicionar JavaScript a uma página específica:

1. Crie um arquivo em `static/js/nome-do-arquivo.js`
2. No template, adicione no bloco extra_js:

```html
{% block extra_js %}
<script src="{{ url_for('static', filename='js/nome-do-arquivo.js') }}"></script>
{% endblock %}
```

## Benefícios da Separação

✅ **Manutenibilidade**: Código mais fácil de encontrar e editar
✅ **Reutilização**: CSS e JS podem ser compartilhados entre páginas
✅ **Performance**: Arquivos podem ser cacheados pelo navegador
✅ **Organização**: Separação clara de responsabilidades (HTML/CSS/JS)
✅ **Desenvolvimento**: Melhor suporte de IDEs com arquivos separados
