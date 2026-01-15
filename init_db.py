"""
Script de inicialização do banco de dados
Execute este arquivo para criar as tabelas do banco de dados
"""

from app import app, db

if __name__ == "__main__":
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        print("✓ Banco de dados criado com sucesso!")
        print("✓ Tabelas criadas: Admin, Funcionario, Folga, Ferias, DiaBloqueado")
        print("\nVocê pode agora executar o aplicativo com: python app.py")
