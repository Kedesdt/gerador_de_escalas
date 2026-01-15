from app import app
from models import Funcionario, EscalaDiaria, Folga, FaixaHorario
from datetime import datetime
from escala_generator import gerar_escalas_com_faixas_horario

app.app_context().push()

# Gerar escalas para Janeiro/2026
print("Gerando escalas com nova lógica de combinações...")
resultado = gerar_escalas_com_faixas_horario(1, 2026, 1)
print(f"Resultado: {resultado}")

# Verificar dia 23/01 (dia da folga do Durval)
data_teste = datetime(2026, 1, 23).date()

print(f"\n=== Análise do dia 23/01/2026 (Durval de folga) ===\n")

# Ver quem está de folga
folgas = Folga.query.filter_by(data=data_teste).all()
print("Funcionários de folga:")
for folga in folgas:
    func = Funcionario.query.get(folga.funcionario_id)
    print(f"  - {func.nome}")

# Ver escalas do dia
print("\nEscalas alocadas:")
escalas = EscalaDiaria.query.filter_by(data=data_teste).all()
for escala in escalas:
    func = Funcionario.query.get(escala.funcionario_id)
    faixa = FaixaHorario.query.get(escala.faixa_horario_id)
    print(f"  - {func.nome}: {faixa.hora_inicio}-{faixa.hora_fim}")

# Ver faixas sem cobertura
print("\nFaixas disponíveis mas não alocadas:")
faixas_ativas = FaixaHorario.query.filter_by(
    admin_id=1, ativo=True, ativo_semana=True
).all()
escalas_ids = {e.faixa_horario_id for e in escalas}

for faixa in faixas_ativas:
    if faixa.id not in escalas_ids:
        print(f"  - {faixa.hora_inicio}-{faixa.hora_fim} (SEM COBERTURA)")

# Verificar se a alocação é ótima
print("\n=== Análise da alocação ===")
print("Esperado: João em 05-11, Vinícius em 11-17 (melhor cobertura)")
print("Ou: Vinícius em 05-11, João em 11-17")
print("\nVerificar se alguma dessas combinações foi escolhida...")
