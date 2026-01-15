from app import app
from models import Funcionario, EscalaDiaria, Folga, FaixaHorario
from datetime import datetime

app.app_context().push()

# Verificar fim de semana: Sábado 17/01/2026 e Domingo 18/01/2026
print("=== VERIFICAÇÃO DOS TURNOS DE FIM DE SEMANA ===\n")

for dia in [17, 18]:
    data_teste = datetime(2026, 1, dia).date()
    dia_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][data_teste.weekday()]

    print(f"\n{dia}/01/2026 ({dia_semana}):")
    print("-" * 50)

    # Ver escalas do dia
    escalas = EscalaDiaria.query.filter_by(data=data_teste).all()

    if not escalas:
        print("  Nenhuma escala alocada")
    else:
        for escala in escalas:
            func = Funcionario.query.get(escala.funcionario_id)
            faixa = FaixaHorario.query.get(escala.faixa_horario_id)
            tipo = "FDS" if faixa.ativo_fds and not faixa.ativo_semana else "SEM"
            print(f"  {func.nome}: {faixa.hora_inicio}-{faixa.hora_fim} [{tipo}]")

print("\n\nFaixas esperadas no FIM DE SEMANA:")
print("  07:00-13:00")
print("  13:00-19:00")
print("  19:00-01:00")
