from app import app
from models import Funcionario, EscalaDiaria, FaixaHorario
from datetime import datetime

app.app_context().push()

# Verificar dia de semana com a nova faixa 17h-23h
data_teste = datetime(2026, 1, 12).date()

print("=== VERIFICAÇÃO DA NOVA FAIXA 17h-23h ===\n")
print(f"Dia 12/01/2026 (Segunda-feira):")
print("-" * 50)

escalas = (
    EscalaDiaria.query.filter_by(data=data_teste)
    .order_by(EscalaDiaria.faixa_horario_id)
    .all()
)

for escala in escalas:
    func = Funcionario.query.get(escala.funcionario_id)
    faixa = FaixaHorario.query.get(escala.faixa_horario_id)
    print(f"  {faixa.hora_inicio}-{faixa.hora_fim}: {func.nome}")

print("\n\nTurnos esperados de SEMANA:")
print("  05:00-11:00")
print("  07:00-13:00")
print("  11:00-17:00")
print("  15:00-21:00")
print("  17:00-23:00 ← NOVA FAIXA")
print("  19:00-01:00")
