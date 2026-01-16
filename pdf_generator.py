from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
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
    Uma semana por página, em formato paisagem
    Colunas: datas e dias da semana
    Linhas: nomes dos funcionários
    """
    buffer = BytesIO()

    # Configurar página em paisagem (landscape)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Estilo personalizado para título
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=11,
        textColor=colors.HexColor("#0d6efd"),
        spaceAfter=2,
        alignment=1,  # Center
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        spaceAfter=3,
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

    # Período da empresa
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

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

    # Dividir o período em semanas
    semanas = []
    data_atual = primeiro_dia

    # Encontrar o primeiro domingo antes ou igual ao primeiro dia
    dias_antes = (data_atual.weekday() + 1) % 7
    inicio_semana = data_atual - timedelta(days=dias_antes)

    data_cursor = inicio_semana
    while data_cursor <= ultimo_dia:
        fim_semana = data_cursor + timedelta(days=6)
        semanas.append((data_cursor, fim_semana))
        data_cursor += timedelta(days=7)

    # Gerar uma página para cada semana
    primeira_pagina = True
    for semana_idx, (data_inicio_semana, data_fim_semana) in enumerate(semanas):
        if not primeira_pagina:
            elements.append(PageBreak())
        primeira_pagina = False

        # Título da página
        titulo = Paragraph(
            f"Escala de Trabalho - {meses_pt[mes-1]} {ano}",
            title_style,
        )
        elements.append(titulo)

        # Período da semana
        data_inicio_str = data_inicio_semana.strftime("%d/%m/%Y")
        data_fim_str = data_fim_semana.strftime("%d/%m/%Y")
        subtitulo = Paragraph(
            f"Semana de {data_inicio_str} a {data_fim_str} | Empresa: {admin_nome}",
            subtitle_style,
        )
        elements.append(subtitulo)
        elements.append(Spacer(1, 1))

        # Criar cabeçalho da tabela (datas e dias da semana)
        header = ["Funcionário"]
        datas_semana = []
        data_col = data_inicio_semana
        while data_col <= data_fim_semana:
            if primeiro_dia <= data_col <= ultimo_dia:
                dia_semana = cal.day_name[data_col.weekday()]
                dia_semana_pt = {
                    "Monday": "Seg",
                    "Tuesday": "Ter",
                    "Wednesday": "Qua",
                    "Thursday": "Qui",
                    "Friday": "Sex",
                    "Saturday": "Sáb",
                    "Sunday": "Dom",
                }[dia_semana]
                header.append(
                    f"{data_col.day:02d}/{data_col.month:02d}\n{dia_semana_pt}"
                )
                datas_semana.append(data_col)
            data_col += timedelta(days=1)

        # Criar linhas da tabela (funcionários)
        data_rows = [header]

        for func in funcionarios:
            row = [func.nome]

            for data_col in datas_semana:
                cell_content = []

                # Verificar se está de férias
                if (data_col, func.id) in ferias_dict:
                    cell_content.append("FÉRIAS")
                # Verificar se está de folga
                elif (data_col, func.id) in folgas_dict:
                    cell_content.append("FOLGA")
                # Verificar se tem escalas
                elif (data_col, func.id) in escalas_dict:
                    escalas_dia = escalas_dict[(data_col, func.id)]
                    for escala in escalas_dia:
                        faixa = next(
                            (
                                f
                                for f in faixas_horario
                                if f.id == escala.faixa_horario_id
                            ),
                            None,
                        )
                        if faixa:
                            horario = f"{faixa.hora_inicio}-{faixa.hora_fim}"
                            cell_content.append(horario)
                else:
                    cell_content.append("-")

                row.append("\n".join(cell_content))

            data_rows.append(row)

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
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 0), (-1, 0), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
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
        for row_idx, func in enumerate(funcionarios, start=1):
            for col_idx, data_col in enumerate(datas_semana, start=1):
                # Verificar se é dia bloqueado
                if data_col in dias_bloqueados_set:
                    table_style.add(
                        "BACKGROUND",
                        (col_idx, row_idx),
                        (col_idx, row_idx),
                        colors.HexColor("#f8d7da"),
                    )
                # Verificar férias
                elif (data_col, func.id) in ferias_dict:
                    table_style.add(
                        "BACKGROUND",
                        (col_idx, row_idx),
                        (col_idx, row_idx),
                        colors.HexColor("#fff3cd"),
                    )
                # Verificar folga
                elif (data_col, func.id) in folgas_dict:
                    table_style.add(
                        "BACKGROUND",
                        (col_idx, row_idx),
                        (col_idx, row_idx),
                        colors.HexColor("#d1e7dd"),
                    )

        table.setStyle(table_style)
        elements.append(table)

        # Adicionar legenda apenas na primeira página
        if semana_idx == 0:
            elements.append(Spacer(1, 2))
            legenda_style = ParagraphStyle(
                "Legenda",
                parent=styles["Normal"],
                fontSize=6,
                textColor=colors.grey,
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

    # Construir PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer
