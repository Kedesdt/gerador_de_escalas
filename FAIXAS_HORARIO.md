# Sistema de Faixas de Horário - Documentação

## Visão Geral

O sistema foi expandido para incluir gestão de faixas de horário e disponibilidade dos funcionários, permitindo alocação automática e realocação inteligente quando há folgas.

## Novas Tabelas

### 1. FaixaHorario

Define as faixas de horário de trabalho na empresa.

**Campos:**

- `id`: Identificador único
- `admin_id`: Admin que criou a faixa
- `hora_inicio`: Horário de início (ex: "05:00")
- `hora_fim`: Horário de fim (ex: "11:00")
- `ordem`: Ordem de exibição
- `ativo`: Se a faixa está ativa

**Exemplo:**

```
05:00 às 11:00
07:00 às 13:00
11:00 às 17:00
15:00 às 21:00
19:00 às 01:00
```

### 2. DisponibilidadeFuncionario

Define quais faixas de horário cada funcionário pode trabalhar.

**Campos:**

- `id`: Identificador único
- `funcionario_id`: Funcionário
- `faixa_horario_id`: Faixa de horário que ele pode cobrir

**Exemplo:**

- João pode trabalhar em: 05:00-11:00 e 07:00-13:00
- Maria pode trabalhar em: 07:00-13:00 e 11:00-17:00

### 3. EscalaDiaria

Define qual funcionário está em qual faixa de horário em cada dia.

**Campos:**

- `id`: Identificador único
- `funcionario_id`: Funcionário alocado
- `faixa_horario_id`: Faixa de horário
- `data`: Data da escala

**Exemplo:**

- 14/01/2026 - 05:00-11:00: João
- 14/01/2026 - 07:00-13:00: Maria
- 14/01/2026 - 11:00-17:00: Pedro

## Funcionalidades

### 1. Geração de Escalas com Faixas

`gerar_escalas_com_faixas_horario(admin_id, ano, mes)`

Gera a escala diária alocando funcionários nas faixas de horário:

- Garante que todas as faixas estejam cobertas
- Respeita folgas e férias
- Considera apenas funcionários com disponibilidade para cada faixa

### 2. Realocação Automática

`realocar_horarios_por_folga(data, funcionario_id_folga, admin_id)`

Quando um funcionário entra de folga:

1. Identifica quais faixas de horário ele cobria naquele dia
2. Busca substitutos com disponibilidade para aquela faixa
3. Prioriza remanejamento (funcionários já trabalhando no dia)
4. Se não encontrar substituto, a faixa fica descoberta (alerta para o admin)

## Exemplo de Uso

### Cenário 1: Folga Simples

```
Funcionário: Pedro (11:00-17:00)
Data: 15/01/2026
Status: De folga

Sistema:
1. Remove Pedro da escala das 11:00-17:00
2. Busca quem tem disponibilidade para 11:00-17:00
3. Encontra Maria (que pode trabalhar nesta faixa)
4. Realoca Maria de 07:00-13:00 para 11:00-17:00
5. Busca substituto para 07:00-13:00
6. Aloca João (se disponível)
```

### Cenário 2: Sem Substituto

```
Funcionário: Ana (única com disponibilidade para 15:00-21:00)
Data: 15/01/2026
Status: De férias

Sistema:
1. Remove Ana da escala das 15:00-21:00
2. Busca substitutos
3. Não encontra ninguém disponível
4. Faixa fica descoberta (admin precisa resolver manualmente)
```

## Migração do Banco

### Passo 1: Recriar Banco

```bash
python init_db_novo.py
```

### Passo 2: Popular com Dados de Exemplo (Opcional)

```bash
python popular_dados_exemplo.py
```

## Próximos Passos

1. **Interface Admin:**

   - Tela para criar/editar faixas de horário
   - Tela para definir disponibilidade dos funcionários
   - Visualização da escala diária com faixas

2. **Alertas:**

   - Notificar quando uma faixa ficar descoberta
   - Sugerir funcionários para realocação

3. **Rodízio:**

   - Implementar lógica de rodízio justo
   - Evitar que sempre o mesmo funcionário seja realocado

4. **Relatórios:**
   - Horas trabalhadas por funcionário
   - Cobertura de faixas de horário
   - Análise de disponibilidade
