from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    funcionarios = db.relationship(
        "Funcionario", backref="admin", lazy=True, cascade="all, delete-orphan"
    )
    dias_bloqueados = db.relationship(
        "DiaBloqueado", backref="admin", lazy=True, cascade="all, delete-orphan"
    )
    faixas_horario = db.relationship(
        "FaixaHorario", backref="admin", lazy=True, cascade="all, delete-orphan"
    )

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Admin {self.nome}>"


class Funcionario(db.Model):
    __tablename__ = "funcionario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preferencia_folga = db.Column(db.String(20))  # 'segunda', 'terca', 'quarta', etc.
    horario_inicio = db.Column(
        db.String(5), nullable=False
    )  # '08:00' (para compatibilidade)
    horario_fim = db.Column(
        db.String(5), nullable=False
    )  # '17:00' (para compatibilidade)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    folgas = db.relationship(
        "Folga", backref="funcionario", lazy=True, cascade="all, delete-orphan"
    )
    ferias = db.relationship(
        "Ferias", backref="funcionario", lazy=True, cascade="all, delete-orphan"
    )
    disponibilidades = db.relationship(
        "DisponibilidadeFuncionario",
        backref="funcionario",
        lazy=True,
        cascade="all, delete-orphan",
    )
    escalas_diarias = db.relationship(
        "EscalaDiaria", backref="funcionario", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Funcionario {self.nome}>"


class Folga(db.Model):
    __tablename__ = "folga"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionario.id"), nullable=False
    )
    data = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Folga {self.funcionario.nome} - {self.data}>"


class Ferias(db.Model):
    __tablename__ = "ferias"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionario.id"), nullable=False
    )
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Ferias {self.funcionario.nome} - {self.data_inicio} a {self.data_fim}>"
        )


class DiaBloqueado(db.Model):
    __tablename__ = "dia_bloqueado"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DiaBloqueado {self.data}>"


class FaixaHorario(db.Model):
    """Faixas de horário de trabalho definidas pelo admin"""

    __tablename__ = "faixa_horario"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=False)
    hora_inicio = db.Column(db.String(5), nullable=False)  # '05:00'
    hora_fim = db.Column(db.String(5), nullable=False)  # '11:00'
    ordem = db.Column(db.Integer, default=0)  # Para ordenação
    ativo = db.Column(db.Boolean, default=True)
    ativo_semana = db.Column(db.Boolean, default=True)  # Ativa em dias de semana
    ativo_fds = db.Column(db.Boolean, default=True)  # Ativa em fins de semana
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    disponibilidades = db.relationship(
        "DisponibilidadeFuncionario",
        backref="faixa_horario",
        lazy=True,
        cascade="all, delete-orphan",
    )
    escalas_diarias = db.relationship(
        "EscalaDiaria", backref="faixa_horario", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FaixaHorario {self.hora_inicio}-{self.hora_fim}>"


class DisponibilidadeFuncionario(db.Model):
    """Define quais faixas de horário cada funcionário pode trabalhar"""

    __tablename__ = "disponibilidade_funcionario"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionario.id"), nullable=False
    )
    faixa_horario_id = db.Column(
        db.Integer, db.ForeignKey("faixa_horario.id"), nullable=False
    )
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Disponibilidade {self.funcionario.nome} - {self.faixa_horario.hora_inicio}-{self.faixa_horario.hora_fim}>"


class EscalaDiaria(db.Model):
    """Define qual funcionário está em qual faixa de horário em cada dia"""

    __tablename__ = "escala_diaria"

    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(
        db.Integer, db.ForeignKey("funcionario.id"), nullable=False
    )
    faixa_horario_id = db.Column(
        db.Integer, db.ForeignKey("faixa_horario.id"), nullable=False
    )
    data = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Constraint única para evitar duplicatas
    # __table_args__ = (
    #    db.UniqueConstraint("faixa_horario_id", "data", name="_faixa_data_uc"),
    # )
    # Retirada a constraint para permitir múltiplos funcionários na mesma faixa

    def __repr__(self):
        return f"<EscalaDiaria {self.funcionario.nome} - {self.data} {self.faixa_horario.hora_inicio}-{self.faixa_horario.hora_fim}>"


class Alerta(db.Model):
    """Alertas do sistema (falta de cobertura, excesso de dias trabalhados, etc)"""

    __tablename__ = "alerta"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'excesso_dias', 'sem_cobertura'
    severidade = db.Column(
        db.String(20), default="alerta"
    )  # 'info', 'alerta', 'critico'
    mensagem = db.Column(db.Text, nullable=False)
    data_referencia = db.Column(db.Date)  # Data à qual o alerta se refere
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionario.id"))  # Opcional
    faixa_horario_id = db.Column(
        db.Integer, db.ForeignKey("faixa_horario.id")
    )  # Opcional
    resolvido = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    admin = db.relationship("Admin", backref="alertas")
    funcionario = db.relationship("Funcionario", backref="alertas")
    faixa_horario = db.relationship("FaixaHorario", backref="alertas")

    def __repr__(self):
        return f"<Alerta {self.tipo} - {self.mensagem[:30]}>"
