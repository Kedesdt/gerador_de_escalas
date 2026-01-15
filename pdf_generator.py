from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
from datetime import datetime, timedelta
import calendar as cal


def gerar_pdf_escala(
    admin_nome,
    ano,
    mes,
    funcionarios,
    escalas_diarias,
    folgas,
    ferias,
    dias_bloqueados,
    faixas_horario,
):
    """
    Gera um PDF com o calendário de escalas do mês
    """
    buffer = BytesIO()

    # Configurar página em retrato (portrait)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Estilo personalizado para título
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0d6efd"),
        spaceAfter=12,
        alignment=1,  # Center
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=1,
    )

    # Meses em português
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

    # Título
    titulo = Paragraph(f"Escala de Trabalho - {meses_pt[mes-1]} {ano}", title_style)
    elements.append(titulo)

    # Período da empresa
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

    subtitulo = Paragraph(
        f"Período: 12/{mes:02d}/{ano} a 11/{proximo_mes:02d}/{proximo_ano}<br/>"
        f"Empresa: {admin_nome}",
        subtitle_style,
    )
    elements.append(subtitulo)
    elements.append(Spacer(1, 10))

    # Preparar dados para a tabela
    primeiro_dia = datetime(ano, mes, 12).date()
    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    # Criar dicionário de escalas por data e funcionário
    escalas_dict = {}
    for escala in escalas_diarias:
        key = (escala.data, escala.funcionario_id)
        if key not in escalas_dict:
            escalas_dict[key] = []
        escalas_dict[key].append(escala)

    # Dicionário de folgas
    folgas_dict = {(folga.data, folga.funcionario_id) for folga in folgas}

    # Dicionário de férias
    ferias_dict = {}
    for feria in ferias:
        data_atual = feria.data_inicio
        while data_atual <= feria.data_fim:
            ferias_dict[(data_atual, feria.funcionario_id)] = feria
            data_atual += timedelta(days=1)

    # Conjunto de dias bloqueados
    dias_bloqueados_set = {dia.data for dia in dias_bloqueados}

    # Criar cabeçalho da tabela
    header = ["Dia/Func."] + [
        f.nome.split()[0] for f in funcionarios
    ]  # Apenas primeiro nome

    # Criar linhas da tabela
    data_rows = [header]

    data_atual = primeiro_dia
    while data_atual <= ultimo_dia:
        dia_semana = cal.day_name[data_atual.weekday()]
        dia_semana_pt = {
            "Monday": "Seg",
            "Tuesday": "Ter",
            "Wednesday": "Qua",
            "Thursday": "Qui",
            "Friday": "Sex",
            "Saturday": "Sáb",
            "Sunday": "Dom",
        }[dia_semana]

        # Coluna da data
        data_str = f"{data_atual.day:02d}/{data_atual.month:02d}\n{dia_semana_pt}"

        row = [data_str]

        # Para cada funcionário
        for func in funcionarios:
            cell_content = []

            # Verificar se está de férias
            if (data_atual, func.id) in ferias_dict:
                cell_content.append("FÉRIAS")
            # Verificar se está de folga
            elif (data_atual, func.id) in folgas_dict:
                cell_content.append("FOLGA")
            # Verificar se tem escalas
            elif (data_atual, func.id) in escalas_dict:
                escalas_dia = escalas_dict[(data_atual, func.id)]
                for escala in escalas_dia:
                    faixa = next(
                        (f for f in faixas_horario if f.id == escala.faixa_horario_id),
                        None,
                    )
                    if faixa:
                        horario = f"{faixa.hora_inicio}-{faixa.hora_fim}"
                        cell_content.append(horario)
            else:
                cell_content.append("-")

            row.append("\n".join(cell_content))

        data_rows.append(row)
        data_atual += timedelta(days=1)

    # Criar tabela
    table = Table(data_rows, repeatRows=1)

    # Estilo da tabela
    table_style = TableStyle(
        [
            # Cabeçalho
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            # Corpo
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#e7f1ff")),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            (
                "ROWBACKGROUNDS",
                (1, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#f8f9fa")],
            ),
        ]
    )

    # Adicionar cores especiais para folgas, férias e dias bloqueados
    for row_idx, row in enumerate(data_rows[1:], start=1):
        data_str = row[0].split("\n")[0]
        dia, mes_str = data_str.split("/")
        data_ref = datetime(
            ano if int(mes_str) == mes else proximo_ano, int(mes_str), int(dia)
        ).date()

        # Verificar se é dia bloqueado
        if data_ref in dias_bloqueados_set:
            table_style.add(
                "BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#f8d7da")
            )

        # Colorir células individuais
        for col_idx, cell in enumerate(row[1:], start=1):
            if "FÉRIAS" in cell:
                table_style.add(
                    "BACKGROUND",
                    (col_idx, row_idx),
                    (col_idx, row_idx),
                    colors.HexColor("#fff3cd"),
                )
            elif "FOLGA" in cell:
                table_style.add(
                    "BACKGROUND",
                    (col_idx, row_idx),
                    (col_idx, row_idx),
                    colors.HexColor("#d1e7dd"),
                )

    table.setStyle(table_style)
    elements.append(table)

    # Adicionar legenda
    elements.append(Spacer(1, 15))
    legenda_style = ParagraphStyle(
        "Legenda", parent=styles["Normal"], fontSize=8, textColor=colors.grey
    )
    legenda = Paragraph(
        "<b>Legenda:</b> "
        "<font color='#0d6efd'>■</font> Trabalhando | "
        "<font color='#198754'>■</font> Folga | "
        "<font color='#ffc107'>■</font> Férias | "
        "<font color='#dc3545'>■</font> Dia Bloqueado",
        legenda_style,
    )
    elements.append(legenda)

    # Adicionar rodapé com data de geração
    elements.append(Spacer(1, 10))
    rodape = Paragraph(
        f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        ParagraphStyle(
            "Rodape",
            parent=styles["Normal"],
            fontSize=7,
            textColor=colors.grey,
            alignment=1,
        ),
    )
    elements.append(rodape)

    # Construir PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer
