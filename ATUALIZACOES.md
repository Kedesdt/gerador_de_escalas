# 📋 Atualizações do Sistema de Escalas

## ✨ Novas Funcionalidades Implementadas

### 1. Período de Trabalho Personalizado

**O mês da empresa agora vai do dia 12 ao dia 11**

- ✅ Calendário mostra do dia 12 de um mês até o dia 11 do próximo mês
- ✅ Geração automática de escalas considera este período
- ✅ Visualização pública também adaptada
- ✅ Navegação entre meses ajustada

**Exemplo:**

- Janeiro 2026 → 12/01/2026 a 11/02/2026
- Fevereiro 2026 → 12/02/2026 a 11/03/2026

### 2. Distribuição Inteligente de Fins de Semana

**Folgas de fim de semana completo são distribuídas ao longo do mês**

- ✅ Cada funcionário recebe um fim de semana completo por mês
- ✅ Fins de semana são distribuídos entre diferentes funcionários
- ✅ Sistema prioriza ter o máximo de pessoas trabalhando
- ✅ Evita que todos folguem no mesmo fim de semana

**Como funciona:**

1. Sistema identifica todos os fins de semana disponíveis (4 por mês normalmente)
2. Distribui um fim de semana diferente para cada funcionário
3. Se houver mais funcionários que fins de semana, alterna entre eles
4. Considera férias ao fazer a distribuição

**Exemplo com 4 funcionários e 4 fins de semana:**

- FDS 1 (12-13/01): João folga
- FDS 2 (19-20/01): Maria folga
- FDS 3 (26-27/01): Carlos folga
- FDS 4 (02-03/02): Ana folga

**Resultado:** Sempre há 3 pessoas trabalhando nos fins de semana! 🎯

### 3. Melhorias na Geração Automática de Escalas

**Regras Implementadas:**

- ✅ Ninguém folga em dias bloqueados pelo admin
- ✅ Mínimo de 1 folga por semana para cada funcionário
- ✅ 1 fim de semana completo de folga por mês (distribuído)
- ✅ Respeita períodos de férias cadastrados
- ✅ Considera preferências de dia da semana
- ✅ Maximiza o número de pessoas trabalhando

## 🔄 Como Usar as Novas Funcionalidades

### Gerar Escala Automática

1. Acesse **Calendário** no menu admin
2. Verifique o período mostrado (ex: 12/01 a 11/02)
3. Clique em **"Gerar Sugestão de Escala"**
4. O sistema irá:
   - Distribuir 1 fim de semana para cada funcionário
   - Adicionar 1 folga semanal para cada um
   - Respeitar dias bloqueados e férias
   - Maximizar cobertura de pessoal

### Ajustes Manuais

Após gerar a escala, você pode:

- Arrastar funcionários para outros dias
- Bloquear dias específicos
- Adicionar ou remover folgas manualmente

### Visualizar Distribuição

No calendário você verá:

- Dias com fundo amarelo = fins de semana
- Dias com fundo vermelho = bloqueados
- Dias com fundo verde = hoje
- Funcionários em azul = folga
- Funcionários em amarelo = férias

## 📊 Benefícios

### Para a Empresa

- ✅ Sempre tem o máximo de pessoas trabalhando
- ✅ Fins de semana bem distribuídos
- ✅ Menos conflitos de folgas
- ✅ Melhor controle de cobertura

### Para os Funcionários

- ✅ Folgas previsíveis e justas
- ✅ Todo mundo ganha um fim de semana completo
- ✅ Preferências de dia são respeitadas
- ✅ Transparência na visualização

## 🎯 Exemplo Prático

**Cenário:** Empresa com 5 funcionários
**Período:** 12/01/2026 a 11/02/2026
**Fins de semana disponíveis:** 4

**Distribuição:**

1. FDS 12-13/01: João folga → 4 pessoas trabalhando
2. FDS 19-20/01: Maria folga → 4 pessoas trabalhando
3. FDS 26-27/01: Carlos folga → 4 pessoas trabalhando
4. FDS 02-03/02: Ana folga → 4 pessoas trabalhando

**Semana normal:**

- Segunda: Pedro folga (preferência dele)
- Terça: João folga
- Quarta: Maria folga
- Quinta: Carlos folga
- Sexta: Ana folga

**Resultado:** Sempre 4 pessoas trabalhando durante a semana!

## 🚀 Dicas de Uso

1. **Gere a escala no início do mês**

   - Use o botão "Gerar Sugestão de Escala"
   - Revise e ajuste se necessário

2. **Bloqueie dias importantes**

   - Clique no cadeado para bloquear dias onde ninguém pode folgar
   - Exemplo: eventos especiais, datas comemorativas

3. **Cadastre férias com antecedência**

   - Vá em "Férias" no menu
   - O sistema considerará automaticamente ao gerar escalas

4. **Use drag-and-drop para ajustes**

   - Arraste nomes dos funcionários para reorganizar folgas
   - Muito mais rápido que editar manualmente

5. **Compartilhe a visualização pública**
   - Link: http://127.0.0.1:5000/escalas
   - Funcionários podem ver suas escalas sem login

---

**Atualizado em:** 14/01/2026
**Versão:** 2.0
