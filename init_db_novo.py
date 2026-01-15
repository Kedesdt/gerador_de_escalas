"""
Script para recriar o banco de dados com as novas tabelas de faixas de horário
ATENÇÃO: Este script apaga o banco existente!
"""

from app import app
from models import db
import os


def recriar_banco():
    with app.app_context():
        # Apagar banco existente
        db_path = "instance/escalas.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✓ Banco de dados antigo removido: {db_path}")

        # Criar todas as tabelas
        db.create_all()
        print("✓ Banco de dados recriado com sucesso!")
        print("\nNovas tabelas criadas:")
        print("  - admin")
        print("  - funcionario")
        print("  - folga")
        print("  - ferias")
        print("  - dia_bloqueado")
        print("  - faixa_horario (NOVA)")
        print("  - disponibilidade_funcionario (NOVA)")
        print("  - escala_diaria (NOVA)")
        print("  - alerta (NOVA)")


if __name__ == "__main__":
    print("=" * 60)
    print("ATENÇÃO: Este script vai APAGAR o banco de dados existente!")
    print("=" * 60)
    confirma = input("\nTem certeza que deseja continuar? (sim/não): ")

    if confirma.lower() == "sim":
        recriar_banco()
        print("\n✓ Processo concluído!")
    else:
        print("\n✗ Operação cancelada.")
