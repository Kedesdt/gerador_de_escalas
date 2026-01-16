"""
Script para popular o banco de dados com dados de exemplo
Incluindo faixas de horário e disponibilidades
"""

from app import app
from models import (
    db,
    Admin,
    Funcionario,
    FaixaHorario,
    DisponibilidadeFuncionario,
    EscalaDiaria,
    Folga,
    Ferias,
    DiaBloqueado,
)
from escala_generator import gerar_escalas_com_faixas_horario
from datetime import datetime


def popular_dados_exemplo():
    with app.app_context():
        # Limpar dados existentes
        print("Limpando dados existentes...")
        DisponibilidadeFuncionario.query.delete()
        EscalaDiaria.query.delete()
        Folga.query.delete()
        Ferias.query.delete()
        DiaBloqueado.query.delete()
        FaixaHorario.query.delete()
        Funcionario.query.delete()
        Admin.query.delete()
        db.session.commit()
        print("✓ Dados limpos")

        # Criar admin
        admin = Admin(nome="Administrador", email="admin@empresa.com")
        admin.definir_senha("admin123")
        db.session.add(admin)
        db.session.commit()
        print(f"✓ Admin criado: {admin.email}")

        # Criar faixas de horário
        faixas = [
            # Faixas de SEMANA
            {
                "hora_inicio": "05:00",
                "hora_fim": "11:00",
                "ordem": 1,
                "ativo_semana": True,
                "ativo_fds": False,
            },
            {
                "hora_inicio": "07:00",
                "hora_fim": "13:00",
                "ordem": 2,
                "ativo_semana": True,
                "ativo_fds": False,
            },
            {
                "hora_inicio": "11:00",
                "hora_fim": "17:00",
                "ordem": 3,
                "ativo_semana": True,
                "ativo_fds": False,
            },
            {
                "hora_inicio": "15:00",
                "hora_fim": "21:00",
                "ordem": 4,
                "ativo_semana": True,
                "ativo_fds": False,
            },
            {
                "hora_inicio": "17:00",
                "hora_fim": "23:00",
                "ordem": 5,
                "ativo_semana": True,
                "ativo_fds": False,
            },
            {
                "hora_inicio": "19:00",
                "hora_fim": "01:00",
                "ordem": 6,
                "ativo_semana": True,
                "ativo_fds": False,
            },
            # Faixas de FIM DE SEMANA (diferentes)
            {
                "hora_inicio": "07:00",
                "hora_fim": "13:00",
                "ordem": 7,
                "ativo_semana": False,
                "ativo_fds": True,
            },
            {
                "hora_inicio": "13:00",
                "hora_fim": "19:00",
                "ordem": 8,
                "ativo_semana": False,
                "ativo_fds": True,
            },
            {
                "hora_inicio": "19:00",
                "hora_fim": "01:00",
                "ordem": 9,
                "ativo_semana": False,
                "ativo_fds": True,
            },
        ]

        faixas_criadas = []
        for f in faixas:
            faixa = FaixaHorario(
                admin_id=admin.id,
                hora_inicio=f["hora_inicio"],
                hora_fim=f["hora_fim"],
                ordem=f["ordem"],
                ativo_semana=f["ativo_semana"],
                ativo_fds=f["ativo_fds"],
            )
            db.session.add(faixa)
            faixas_criadas.append(faixa)

        db.session.commit()
        print(f"✓ {len(faixas_criadas)} faixas de horário criadas")

        # Criar funcionários
        # Índices das faixas: 0=05-11(sem), 1=07-13(sem), 2=11-17(sem), 3=15-21(sem), 4=17-23(sem), 5=19-01(sem)
        #                     6=07-13(fds), 7=13-19(fds), 8=19-01(fds)
        funcionarios_data = [
            {
                "nome": "Gilberto",
                "preferencia": "segunda",
                "horario": "15:00-01:00",
                "faixas": [
                    3,
                    4,
                    5,
                    7,
                    8,
                ],  # Semana: 15-21, 17-23, 19-01 | FDS: 13-19, 19-01
            },
            {
                "nome": "João",
                "preferencia": "quarta",
                "horario": "05:00-13:00",
                "faixas": [0, 1, 6],  # Semana: 05-11, 07-13 | FDS: 07-13
            },
            {
                "nome": "Vinícius",
                "preferencia": "terca",
                "horario": "05:00-17:00",
                "faixas": [
                    0,
                    1,
                    2,
                    6,
                    7,
                ],  # Semana: 05-11, 07-13, 11-17 | FDS: 07-13, 13-19
            },
            {
                "nome": "Alisson",
                "preferencia": "quinta",
                "horario": "13:00-01:00",
                "faixas": [
                    3,
                    4,
                    5,
                    7,
                    8,
                ],  # Semana: 15-21, 17-23, 19-01 | FDS: 13-19, 19-01
            },
            {
                "nome": "Durval",
                "preferencia": "sexta",
                "horario": "11:00-21:00",
                "faixas": [2, 3, 7],  # Semana: 11-17 | FDS: 13-19
            },
        ]

        funcionarios_criados = []
        for f_data in funcionarios_data:
            func = Funcionario(
                nome=f_data["nome"],
                preferencia_folga=f_data["preferencia"],
                horario_inicio=f_data["horario"].split("-")[0],
                horario_fim=f_data["horario"].split("-")[1],
                admin_id=admin.id,
            )
            db.session.add(func)
            db.session.commit()  # Commit para pegar o ID

            # Adicionar disponibilidades
            for idx_faixa in f_data["faixas"]:
                disp = DisponibilidadeFuncionario(
                    funcionario_id=func.id,
                    faixa_horario_id=faixas_criadas[idx_faixa].id,
                )
                db.session.add(disp)

            funcionarios_criados.append(func)

        db.session.commit()
        print(
            f"✓ {len(funcionarios_criados)} funcionários criados com suas disponibilidades"
        )

        print("\n" + "=" * 60)
        print("RESUMO DOS DADOS CRIADOS")
        print("=" * 60)
        print(f"\nAdmin: {admin.email} (senha: admin123)")

        print("\nFaixas de Horário - SEMANA:")
        for faixa in faixas_criadas:
            if faixa.ativo_semana:
                print(f"  {faixa.hora_inicio} às {faixa.hora_fim}")

        print("\nFaixas de Horário - FIM DE SEMANA:")
        for faixa in faixas_criadas:
            if faixa.ativo_fds:
                print(f"  {faixa.hora_inicio} às {faixa.hora_fim}")

        print("\nFuncionários e Disponibilidades:")
        for func in funcionarios_criados:
            disponibilidades = DisponibilidadeFuncionario.query.filter_by(
                funcionario_id=func.id
            ).all()
            faixas_disp = [
                f"{d.faixa_horario.hora_inicio}-{d.faixa_horario.hora_fim}"
                for d in disponibilidades
            ]
            print(f"  {func.nome}: {', '.join(faixas_disp)}")

        # Gerar escalas para o mês atual
        print("\n" + "=" * 60)
        print("GERANDO ESCALAS PARA O MÊS ATUAL")
        print("=" * 60)

        hoje = datetime.now()
        try:
            resultado = gerar_escalas_com_faixas_horario(
                admin.id, hoje.year, hoje.month
            )
            print(f"✓ {resultado['mensagem']}")
        except Exception as e:
            print(f"✗ Erro ao gerar escalas: {e}")


if __name__ == "__main__":
    popular_dados_exemplo()
    print("\n✓ Processo concluído!")
