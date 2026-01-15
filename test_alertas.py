from app import app
from escala_generator import verificar_alertas_escalas

app.app_context().push()

alertas = verificar_alertas_escalas(1, 2026, 1)
alertas_cobertura = [a for a in alertas if a["tipo"] == "sem_cobertura"]

print(f"Total de alertas de cobertura: {len(alertas_cobertura)}\n")

for a in alertas_cobertura[:10]:
    print(f"{a['data_referencia']}: {a['mensagem']}")
