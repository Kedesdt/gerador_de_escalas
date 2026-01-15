from app import app
from models import Funcionario, EscalaDiaria, Folga, FaixaHorario
from datetime import datetime

app.app_context().push()

# Verificar dia de semana: Segunda 12/01/2026
# Verificar fim de semana: Sábado 17/01/2026
print("=== COMPARAÇÃO SEMANA vs FIM DE SEMANA ===\n")

dados = [
    (12, "Segunda"),
    (17, "Sábado"),
]

for dia, nome_dia in dados:
    data_teste = datetime(2026, 1, dia).date()

    print(f"\n{dia}/01/2026 ({nome_dia}):")
    print("-" * 50)

    escalas = (
        EscalaDiaria.query.filter_by(data=data_teste)
        .order_by(EscalaDiaria.faixa_horario_id)
        .all()
    )

    if not escalas:
        print("  Nenhuma escala alocada")
    else:
        for escala in escalas:
            func = Funcionario.query.get(escala.funcionario_id)
            faixa = FaixaHorario.query.get(escala.faixa_horario_id)
            print(f"  {faixa.hora_inicio}-{faixa.hora_fim}: {func.nome}")

print("\n\n" + "=" * 50)
print("RESUMO:")
print("=" * 50)
print("\nTurnos de SEMANA (Segunda a Sexta):")
print("  05:00-11:00")
print("  07:00-13:00")
print("  11:00-17:00")
print("  15:00-21:00")
print("  19:00-01:00")

print("\nTurnos de FIM DE SEMANA (Sábado e Domingo):")
print("  07:00-13:00")
print("  13:00-19:00")
print("  19:00-01:00")
