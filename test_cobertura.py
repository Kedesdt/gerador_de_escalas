from app import app
from models import FaixaHorario

app.app_context().push()


def str_to_minutes(hora_str):
    h, m = hora_str.split(":")
    minutos = int(h) * 60 + int(m)
    # Apenas horários de madrugada (01:00-05:00) são considerados do dia seguinte
    if minutos < 120:  # Apenas 00:00 e 01:00
        minutos += 24 * 60
    return minutos


faixas = FaixaHorario.query.filter_by(ativo=True, ativo_semana=True).all()
faixa_7_13 = [f for f in faixas if f.hora_inicio == "07:00"][0]

inicio_faixa = str_to_minutes(faixa_7_13.hora_inicio)
fim_faixa = str_to_minutes(faixa_7_13.hora_fim)
duracao_faixa = fim_faixa - inicio_faixa

minutos_faixa = set(range(inicio_faixa, fim_faixa))
minutos_cobertos_por_outras = set()

print(f"Analisando faixa {faixa_7_13.hora_inicio}-{faixa_7_13.hora_fim}")
print(f"Minutos: {inicio_faixa}-{fim_faixa} = {len(minutos_faixa)} minutos")
print(
    f"Minutos reais: {list(sorted(minutos_faixa))[:5]}...{list(sorted(minutos_faixa))[-5:]}"
)
print()

for outra_faixa in faixas:
    if outra_faixa.id == faixa_7_13.id:
        continue

    inicio_outra = str_to_minutes(outra_faixa.hora_inicio)
    fim_outra = str_to_minutes(outra_faixa.hora_fim)
    minutos_outra = set(range(inicio_outra, fim_outra))

    intersecao = minutos_faixa & minutos_outra
    minutos_cobertos_por_outras.update(intersecao)

    print(
        f"{outra_faixa.hora_inicio}-{outra_faixa.hora_fim}: {inicio_outra}-{fim_outra}, +{len(intersecao)} minutos, total coberto={len(minutos_cobertos_por_outras)}"
    )

percentual_coberto = (len(minutos_cobertos_por_outras) / duracao_faixa) * 100
print()
print(
    f"Total coberto: {len(minutos_cobertos_por_outras)}/{duracao_faixa} = {percentual_coberto:.1f}%"
)
