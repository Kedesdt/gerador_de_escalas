# 🎯 Guia Rápido de Uso

## ✅ Sistema está rodando!

O servidor Flask está ativo em: **http://127.0.0.1:5000**

## 📋 Próximos Passos

### 1. Primeiro Acesso

1. Abra seu navegador
2. Acesse: http://127.0.0.1:5000
3. Você será redirecionado para criar sua conta de admin
4. Preencha seus dados e clique em "Cadastrar"

### 2. Adicionar Funcionários

1. Após fazer login, clique em "Funcionários" no menu
2. Clique no botão "Novo Funcionário"
3. Preencha:
   - Nome do funcionário
   - Preferência de folga (dia da semana que ele prefere folgar)
   - Horário de início do trabalho
   - Horário de término do trabalho
4. Clique em "Salvar"

### 3. Gerenciar Escalas no Calendário

1. Clique em "Calendário" no menu
2. Você verá o calendário do mês atual
3. **Para adicionar folga manualmente:**
   - Arraste o nome do funcionário da lista superior
   - Solte sobre o dia desejado no calendário
4. **Para bloquear um dia (ninguém pode folgar):**
   - Clique no ícone de cadeado no canto superior direito do dia
5. **Para gerar escala automaticamente:**
   - Clique no botão "Gerar Sugestão de Escala"
   - O sistema criará folgas respeitando todas as regras

### 4. Cadastrar Férias

1. Clique em "Férias" no menu
2. Clique em "Cadastrar Férias"
3. Selecione o funcionário
4. Escolha as datas de início e fim
5. Clique em "Salvar"

### 5. Visualizar Escalas (Painel Público)

1. Clique em "Visualização Pública" no menu
2. Veja o calendário com o status de todos os funcionários:
   - **Verde**: Funcionário trabalhando
   - **Azul**: Funcionário de folga
   - **Amarelo**: Funcionário de férias

## 🎨 Recursos Visuais

### Calendário Admin (com Drag & Drop)

- Arraste e solte funcionários nos dias
- Botão de bloqueio em cada dia
- Cores diferentes para fins de semana, dias bloqueados e hoje

### Calendário de Visualização

- Apenas leitura
- Mostra todos os funcionários e seus status
- Ideal para compartilhar com a equipe

## 🔧 Dicas

1. **Gere a escala uma vez por mês** usando o botão automático
2. **Ajuste manualmente** se necessário usando drag & drop
3. **Bloqueie dias importantes** onde todos devem trabalhar
4. **Cadastre férias com antecedência** para o sistema considerar na geração

## 🛑 Para Parar o Servidor

Pressione `Ctrl + C` no terminal onde o servidor está rodando

## 🔄 Para Reiniciar

Execute novamente:

```powershell
python app.py
```

## 📱 Compartilhar com a Equipe

1. Envie o link da visualização pública para seus funcionários
2. Eles podem acessar sem login em: http://127.0.0.1:5000/escalas
3. Se precisar acessar de outro computador na mesma rede:
   - Use o IP da máquina no lugar de 127.0.0.1
   - Exemplo: http://192.168.1.100:5000/escalas

---

## ⚙️ Regras Automáticas do Sistema

Quando você clica em "Gerar Sugestão de Escala", o sistema:

✅ Garante **1 folga por semana** para cada funcionário  
✅ Dá **1 fim de semana completo** de folga por mês  
✅ Respeita a **preferência de dia** de cada funcionário  
✅ **Nunca coloca folga** em dias bloqueados  
✅ **Considera períodos de férias** automaticamente

Divirta-se gerenciando suas escalas! 🎉
