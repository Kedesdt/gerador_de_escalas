from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_file,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from models import (
    db,
    Admin,
    Funcionario,
    Folga,
    Ferias,
    DiaBloqueado,
    EscalaDiaria,
    FaixaHorario,
    Alerta,
)
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import calendar
from escala_generator import (
    gerar_sugestao_escalas,
    realocar_horarios_por_folga,
    gerar_escalas_com_faixas_horario,
    verificar_alertas_escalas,
)

try:
    from pdf_generator import gerar_pdf_escala

    PDF_DISPONIVEL = True
except ImportError:
    PDF_DISPONIVEL = False
    print("AVISO: ReportLab não instalado. Exportação de PDF desabilitada.")

app = Flask(__name__)
app.config["SECRET_KEY"] = "sua-chave-secreta-aqui-mude-em-producao"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///escalas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Adicionar funções personalizadas ao Jinja2
@app.template_filter("weekday")
def weekday_filter(date_obj):
    """Retorna o dia da semana (0=segunda, 6=domingo)"""
    return date_obj.weekday()


@app.template_filter("monthrange")
def monthrange_filter(year, month):
    """Retorna o último dia do mês"""
    return calendar.monthrange(year, month)[1]


@app.template_filter("from_ordinal")
def from_ordinal_filter(ordinal):
    """Converte ordinal para data"""
    from datetime import date

    return date.fromordinal(int(ordinal))


app.jinja_env.globals.update(now=datetime.now, calendar=calendar)


@app.template_filter("monthrange")
def monthrange_filter(year, month):
    """Retorna o último dia do mês"""
    return calendar.monthrange(year, month)[1]


app.jinja_env.globals.update(now=datetime.now, calendar=calendar)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# Rotas de Autenticação
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        admin = Admin.query.filter_by(email=email).first()

        if admin and admin.verificar_senha(senha):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Email ou senha inválidos", "danger")

    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        if Admin.query.filter_by(email=email).first():
            flash("Email já cadastrado", "danger")
            return redirect(url_for("registro"))

        novo_admin = Admin(nome=nome, email=email)
        novo_admin.definir_senha(senha)
        db.session.add(novo_admin)
        db.session.commit()

        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# Painel Admin
@app.route("/admin")
@login_required
def admin_dashboard():
    funcionarios = Funcionario.query.filter_by(admin_id=current_user.id).all()
    return render_template("admin/dashboard.html", funcionarios=funcionarios)


@app.route("/admin/funcionarios")
@login_required
def listar_funcionarios():
    funcionarios = Funcionario.query.filter_by(admin_id=current_user.id).all()
    return render_template("admin/funcionarios.html", funcionarios=funcionarios)


@app.route("/admin/funcionario/novo", methods=["GET", "POST"])
@login_required
def novo_funcionario():
    if request.method == "POST":
        nome = request.form.get("nome")
        preferencia_folga = request.form.get("preferencia_folga")
        horario_inicio = request.form.get("horario_inicio")
        horario_fim = request.form.get("horario_fim")

        funcionario = Funcionario(
            nome=nome,
            preferencia_folga=preferencia_folga,
            horario_inicio=horario_inicio,
            horario_fim=horario_fim,
            admin_id=current_user.id,
        )
        db.session.add(funcionario)
        db.session.commit()

        flash("Funcionário cadastrado com sucesso!", "success")
        return redirect(url_for("listar_funcionarios"))

    return render_template("admin/funcionario_form.html")


@app.route("/admin/funcionario/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)

    if funcionario.admin_id != current_user.id:
        flash("Acesso negado", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        funcionario.nome = request.form.get("nome")
        funcionario.preferencia_folga = request.form.get("preferencia_folga")
        funcionario.horario_inicio = request.form.get("horario_inicio")
        funcionario.horario_fim = request.form.get("horario_fim")
        db.session.commit()

        flash("Funcionário atualizado com sucesso!", "success")
        return redirect(url_for("listar_funcionarios"))

    return render_template("admin/funcionario_form.html", funcionario=funcionario)


@app.route("/admin/funcionario/<int:id>/excluir", methods=["POST"])
@login_required
def excluir_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)

    if funcionario.admin_id != current_user.id:
        return jsonify({"erro": "Acesso negado"}), 403

    db.session.delete(funcionario)
    db.session.commit()

    flash("Funcionário excluído com sucesso!", "success")
    return redirect(url_for("listar_funcionarios"))


# Calendário de Escalas
@app.route("/admin/calendario")
@login_required
def calendario():
    ano = request.args.get("ano", datetime.now().year, type=int)
    mes = request.args.get("mes", datetime.now().month, type=int)

    funcionarios = Funcionario.query.filter_by(admin_id=current_user.id).all()

    # Período da empresa: dia 12 do mês até dia 11 do próximo mês
    primeiro_dia = datetime(ano, mes, 12).date()

    # Calcular próximo mês
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    folgas = (
        Folga.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == current_user.id,
            Folga.data >= primeiro_dia,
            Folga.data <= ultimo_dia,
        )
        .all()
    )

    dias_bloqueados = DiaBloqueado.query.filter(
        DiaBloqueado.admin_id == current_user.id,
        DiaBloqueado.data >= primeiro_dia,
        DiaBloqueado.data <= ultimo_dia,
    ).all()

    ferias = (
        Ferias.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == current_user.id,
            or_(
                and_(Ferias.data_inicio <= ultimo_dia, Ferias.data_fim >= primeiro_dia)
            ),
        )
        .all()
    )

    # Buscar escalas diárias do período
    escalas_diarias = (
        EscalaDiaria.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == current_user.id,
            EscalaDiaria.data >= primeiro_dia,
            EscalaDiaria.data <= ultimo_dia,
        )
        .all()
    )

    # Buscar faixas de horário ativas
    faixas_horario = (
        FaixaHorario.query.filter_by(admin_id=current_user.id, ativo=True)
        .order_by(FaixaHorario.ordem)
        .all()
    )

    # Gerar alertas em tempo real
    from escala_generator import verificar_alertas_escalas

    alertas_lista = verificar_alertas_escalas(current_user.id, ano, mes)

    return render_template(
        "admin/calendario.html",
        ano=ano,
        mes=mes,
        primeiro_dia=primeiro_dia,
        ultimo_dia=ultimo_dia,
        funcionarios=funcionarios,
        folgas=folgas,
        dias_bloqueados=dias_bloqueados,
        ferias=ferias,
        escalas_diarias=escalas_diarias,
        faixas_horario=faixas_horario,
        alertas=alertas_lista,
    )


# API para atualizar folgas via drag and drop
@app.route("/api/folga/adicionar", methods=["POST"])
@login_required
def adicionar_folga():
    data = request.json
    funcionario_id = data.get("funcionario_id")
    data_folga = datetime.strptime(data.get("data"), "%Y-%m-%d").date()

    funcionario = Funcionario.query.get(funcionario_id)
    if not funcionario or funcionario.admin_id != current_user.id:
        return jsonify({"erro": "Funcionário não encontrado"}), 404

    # Verificar se dia está bloqueado
    dia_bloqueado = DiaBloqueado.query.filter_by(
        admin_id=current_user.id, data=data_folga
    ).first()

    if dia_bloqueado:
        return jsonify({"erro": "Este dia está bloqueado para folgas"}), 400

    # Verificar se já existe folga
    folga_existente = Folga.query.filter_by(
        funcionario_id=funcionario_id, data=data_folga
    ).first()

    if folga_existente:
        return jsonify({"erro": "Folga já existe para este dia"}), 400

    folga = Folga(funcionario_id=funcionario_id, data=data_folga)
    db.session.add(folga)
    db.session.commit()

    # Realocar horários para cobrir a ausência
    try:
        realocar_horarios_por_folga(data_folga, funcionario_id, current_user.id)
    except Exception as e:
        # Se houver erro na realocação, ainda mantém a folga
        print(f"Erro ao realocar horários: {e}")

    return jsonify({"sucesso": True, "folga_id": folga.id})


@app.route("/api/folga/<int:id>/remover", methods=["DELETE"])
@login_required
def remover_folga(id):
    folga = Folga.query.get(id)
    if not folga or folga.funcionario.admin_id != current_user.id:
        return jsonify({"erro": "Folga não encontrada"}), 404

    db.session.delete(folga)
    db.session.commit()

    return jsonify({"sucesso": True})


# API para gerenciar escalas de turnos
@app.route("/api/escala/adicionar", methods=["POST"])
@login_required
def adicionar_escala():
    data = request.json
    funcionario_id = data.get("funcionario_id")
    faixa_horario_id = data.get("faixa_horario_id")
    data_escala = datetime.strptime(data.get("data"), "%Y-%m-%d").date()

    # Verificar se funcionário pertence ao admin
    funcionario = Funcionario.query.get(funcionario_id)
    if not funcionario or funcionario.admin_id != current_user.id:
        return jsonify({"erro": "Funcionário não encontrado"}), 404

    # Verificar se faixa pertence ao admin
    faixa = FaixaHorario.query.get(faixa_horario_id)
    if not faixa or faixa.admin_id != current_user.id:
        return jsonify({"erro": "Faixa de horário não encontrada"}), 404

    # Verificar se já existe escala para este funcionário neste dia e faixa
    escala_existente = EscalaDiaria.query.filter_by(
        funcionario_id=funcionario_id,
        faixa_horario_id=faixa_horario_id,
        data=data_escala,
    ).first()

    if escala_existente:
        return jsonify({"erro": "Funcionário já está escalado nesta faixa"}), 400

    # Remover folga se existir
    folga_existente = Folga.query.filter_by(
        funcionario_id=funcionario_id, data=data_escala
    ).first()
    if folga_existente:
        db.session.delete(folga_existente)

    # Criar nova escala
    nova_escala = EscalaDiaria(
        funcionario_id=funcionario_id,
        faixa_horario_id=faixa_horario_id,
        data=data_escala,
    )
    db.session.add(nova_escala)
    db.session.commit()

    return jsonify({"sucesso": True, "escala_id": nova_escala.id})


@app.route("/api/escala/<int:id>/remover", methods=["DELETE"])
@login_required
def remover_escala(id):
    escala = EscalaDiaria.query.get(id)
    if not escala or escala.funcionario.admin_id != current_user.id:
        return jsonify({"erro": "Escala não encontrada"}), 404

    db.session.delete(escala)
    db.session.commit()

    return jsonify({"sucesso": True})


@app.route("/api/dia-bloqueado/toggle", methods=["POST"])
@login_required
def toggle_dia_bloqueado():
    data = request.json
    data_bloqueio = datetime.strptime(data.get("data"), "%Y-%m-%d").date()

    dia_bloqueado = DiaBloqueado.query.filter_by(
        admin_id=current_user.id, data=data_bloqueio
    ).first()

    if dia_bloqueado:
        db.session.delete(dia_bloqueado)
        db.session.commit()
        return jsonify({"bloqueado": False})
    else:
        novo_bloqueio = DiaBloqueado(admin_id=current_user.id, data=data_bloqueio)
        db.session.add(novo_bloqueio)
        db.session.commit()
        return jsonify({"bloqueado": True})


# API para marcar alertas como resolvidos
# Férias
@app.route("/admin/ferias")
@login_required
def listar_ferias():
    ferias = (
        Ferias.query.join(Funcionario)
        .filter(Funcionario.admin_id == current_user.id)
        .all()
    )
    return render_template("admin/ferias.html", ferias=ferias)


@app.route("/admin/ferias/nova", methods=["GET", "POST"])
@login_required
def nova_ferias():
    if request.method == "POST":
        funcionario_id = request.form.get("funcionario_id")
        data_inicio = datetime.strptime(
            request.form.get("data_inicio"), "%Y-%m-%d"
        ).date()
        data_fim = datetime.strptime(request.form.get("data_fim"), "%Y-%m-%d").date()

        funcionario = Funcionario.query.get(funcionario_id)
        if not funcionario or funcionario.admin_id != current_user.id:
            flash("Funcionário não encontrado", "danger")
            return redirect(url_for("listar_ferias"))

        ferias = Ferias(
            funcionario_id=funcionario_id, data_inicio=data_inicio, data_fim=data_fim
        )
        db.session.add(ferias)
        db.session.commit()

        flash("Férias cadastradas com sucesso!", "success")
        return redirect(url_for("listar_ferias"))

    funcionarios = Funcionario.query.filter_by(admin_id=current_user.id).all()
    return render_template("admin/ferias_form.html", funcionarios=funcionarios)


# Gerar sugestão de escalas
@app.route("/admin/gerar-escala", methods=["POST"])
@login_required
def gerar_escala():
    data = request.json
    mes = data.get("mes")
    ano = data.get("ano")

    try:
        resultado = gerar_escalas_com_faixas_horario(current_user.id, ano, mes)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400


# Painel de Visualização (público)
@app.route("/")
def index():
    # Verificar se há admin cadastrado (primeiro acesso)
    if Admin.query.count() == 0:
        return redirect(url_for("registro"))
    return redirect(url_for("visualizar_escalas"))


@app.route("/escalas")
def visualizar_escalas():
    ano = request.args.get("ano", datetime.now().year, type=int)
    mes = request.args.get("mes", datetime.now().month, type=int)

    # Buscar todos os funcionários (de todos os admins para visualização pública)
    # Ou você pode filtrar por um admin específico se preferir
    funcionarios = Funcionario.query.all()

    # Período da empresa: dia 12 do mês até dia 11 do próximo mês
    primeiro_dia = datetime(ano, mes, 12).date()

    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    folgas = Folga.query.filter(
        Folga.data >= primeiro_dia, Folga.data <= ultimo_dia
    ).all()

    ferias = Ferias.query.filter(
        or_(and_(Ferias.data_inicio <= ultimo_dia, Ferias.data_fim >= primeiro_dia))
    ).all()

    # Buscar escalas diárias do período
    escalas_diarias = EscalaDiaria.query.filter(
        EscalaDiaria.data >= primeiro_dia, EscalaDiaria.data <= ultimo_dia
    ).all()

    # Gerar alertas em tempo real (se houver admin)
    alertas = []
    if Admin.query.count() > 0:
        admin = Admin.query.first()  # Pegar primeiro admin para visualização pública
        from escala_generator import verificar_alertas_escalas

        alertas = verificar_alertas_escalas(admin.id, ano, mes)

    return render_template(
        "visualizacao.html",
        ano=ano,
        mes=mes,
        primeiro_dia=primeiro_dia,
        ultimo_dia=ultimo_dia,
        funcionarios=funcionarios,
        folgas=folgas,
        ferias=ferias,
        escalas_diarias=escalas_diarias,
        alertas=alertas,
    )


# Exportar PDF
@app.route("/admin/exportar-pdf")
@login_required
def exportar_pdf():
    if not PDF_DISPONIVEL:
        flash("Exportação de PDF não disponível. Instale o ReportLab.", "error")
        return redirect(url_for("calendario"))

    ano = request.args.get("ano", datetime.now().year, type=int)
    mes = request.args.get("mes", datetime.now().month, type=int)

    # Período da empresa
    primeiro_dia = datetime(ano, mes, 12).date()
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano
    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    # Buscar dados
    funcionarios = (
        Funcionario.query.filter_by(admin_id=current_user.id)
        .order_by(Funcionario.nome)
        .all()
    )

    folgas = (
        Folga.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == current_user.id,
            Folga.data >= primeiro_dia,
            Folga.data <= ultimo_dia,
        )
        .all()
    )

    ferias = (
        Ferias.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == current_user.id,
            or_(
                and_(Ferias.data_inicio <= ultimo_dia, Ferias.data_fim >= primeiro_dia)
            ),
        )
        .all()
    )

    dias_bloqueados = DiaBloqueado.query.filter(
        DiaBloqueado.admin_id == current_user.id,
        DiaBloqueado.data >= primeiro_dia,
        DiaBloqueado.data <= ultimo_dia,
    ).all()

    escalas_diarias = (
        EscalaDiaria.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == current_user.id,
            EscalaDiaria.data >= primeiro_dia,
            EscalaDiaria.data <= ultimo_dia,
        )
        .all()
    )

    faixas_horario = FaixaHorario.query.filter_by(admin_id=current_user.id).all()

    # Gerar PDF
    meses_pt = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]

    pdf_buffer = gerar_pdf_escala(
        admin_nome=current_user.nome,
        ano=ano,
        mes=mes,
        funcionarios=funcionarios,
        escalas_diarias=escalas_diarias,
        folgas=folgas,
        ferias=ferias,
        dias_bloqueados=dias_bloqueados,
        faixas_horario=faixas_horario,
    )

    filename = f"Escala_{meses_pt[mes-1]}_{ano}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
