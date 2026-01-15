from datetime import datetime, timedelta
from models import (
    db,
    Funcionario,
    Folga,
    DiaBloqueado,
    Ferias,
    FaixaHorario,
    DisponibilidadeFuncionario,
    EscalaDiaria,
    Alerta,
)
import calendar
from itertools import combinations, permutations


def gerar_sugestao_escalas(admin_id, ano, mes):
    """
    Gera uma sugestão de escalas para o mês especificado seguindo as regras:
    - Ninguém folga em dias bloqueados
    - Mínimo de 1 folga por semana
    - Um fim de semana completo de folga por mês (distribuídos entre funcionários)
    - Respeitar férias
    - Considerar preferências de folga
    - Mês da empresa: dia 12 de um mês até dia 11 do próximo
    """

    # Buscar funcionários do admin
    funcionarios = Funcionario.query.filter_by(admin_id=admin_id, ativo=True).all()

    if not funcionarios:
        raise Exception("Nenhum funcionário cadastrado")

    # Calcular primeiro e último dia do mês da empresa (dia 12 ao dia 11)
    primeiro_dia = datetime(ano, mes, 12).date()

    # Próximo mês para pegar até dia 11
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    # Apagar todas as folgas existentes neste período
    folgas_existentes = (
        Folga.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            Folga.data >= primeiro_dia,
            Folga.data <= ultimo_dia,
        )
        .all()
    )

    for folga in folgas_existentes:
        db.session.delete(folga)

    db.session.commit()

    # Buscar dias bloqueados
    dias_bloqueados = DiaBloqueado.query.filter(
        DiaBloqueado.admin_id == admin_id,
        DiaBloqueado.data >= primeiro_dia,
        DiaBloqueado.data <= ultimo_dia,
    ).all()

    dias_bloqueados_set = set(db.data for db in dias_bloqueados)

    # Buscar férias
    ferias = (
        Ferias.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            Ferias.data_fim >= primeiro_dia,
            Ferias.data_inicio <= ultimo_dia,
        )
        .all()
    )

    # Criar dicionário de férias por funcionário
    ferias_por_funcionario = {}
    for feria in ferias:
        if feria.funcionario_id not in ferias_por_funcionario:
            ferias_por_funcionario[feria.funcionario_id] = []
        ferias_por_funcionario[feria.funcionario_id].append(
            {"inicio": feria.data_inicio, "fim": feria.data_fim}
        )

    novas_folgas = []

    # Coletar todos os fins de semana disponíveis no período
    fins_de_semana_disponiveis = coletar_fins_de_semana(
        primeiro_dia, ultimo_dia, dias_bloqueados_set
    )

    # Distribuir fins de semana entre funcionários para maximizar cobertura
    fins_de_semana_por_funcionario = distribuir_fins_de_semana(
        funcionarios, fins_de_semana_disponiveis, ferias_por_funcionario
    )

    # Para cada funcionário, gerar folgas
    for funcionario in funcionarios:
        fim_de_semana_atribuido = fins_de_semana_por_funcionario.get(funcionario.id)

        folgas_geradas = gerar_folgas_funcionario(
            funcionario,
            primeiro_dia,
            ultimo_dia,
            dias_bloqueados_set,
            ferias_por_funcionario.get(funcionario.id, []),
            fim_de_semana_atribuido,
        )
        novas_folgas.extend(folgas_geradas)

    # Salvar novas folgas
    for folga_data in novas_folgas:
        # Verificar se já existe
        folga_existente = Folga.query.filter_by(
            funcionario_id=folga_data["funcionario_id"], data=folga_data["data"]
        ).first()

        if not folga_existente:
            nova_folga = Folga(
                funcionario_id=folga_data["funcionario_id"], data=folga_data["data"]
            )
            db.session.add(nova_folga)

    db.session.commit()

    return {
        "sucesso": True,
        "folgas_criadas": len(novas_folgas),
        "funcionarios": len(funcionarios),
    }


def coletar_fins_de_semana(primeiro_dia, ultimo_dia, dias_bloqueados):
    """
    Coleta todos os fins de semana completos (sábado + domingo) no período
    """
    fins_de_semana = []
    data_atual = primeiro_dia

    while data_atual <= ultimo_dia:
        # Procurar sábados
        if data_atual.weekday() == 5:  # Sábado
            domingo = data_atual + timedelta(days=1)

            # Verificar se domingo também está no período e ambos não estão bloqueados
            if (
                domingo <= ultimo_dia
                and data_atual not in dias_bloqueados
                and domingo not in dias_bloqueados
            ):

                fins_de_semana.append((data_atual, domingo))

        data_atual += timedelta(days=1)

    return fins_de_semana


def distribuir_fins_de_semana(
    funcionarios, fins_de_semana_disponiveis, ferias_por_funcionario
):
    """
    Distribui fins de semana entre funcionários para garantir que todos tenham um fim de semana
    Permite até 2 funcionários por fim de semana se necessário
    """
    distribuicao = {}
    fins_de_semana_alocados = {i: [] for i in range(len(fins_de_semana_disponiveis))}

    # Se tem mais funcionários que fins de semana, alguns vão compartilhar
    max_por_fds = 1 if len(funcionarios) <= len(fins_de_semana_disponiveis) else 2

    # Primeira passada: tentar dar um fim de semana para cada funcionário
    for func in funcionarios:
        # Encontrar um fim de semana onde este funcionário não está de férias
        # e que ainda tem vaga
        alocado = False

        for idx, (sabado, domingo) in enumerate(fins_de_semana_disponiveis):
            # Verificar se já tem o máximo de pessoas neste fim de semana
            if len(fins_de_semana_alocados[idx]) >= max_por_fds:
                continue

            # Verificar se funcionário está de férias
            ferias_func = ferias_por_funcionario.get(func.id, [])
            em_ferias = False
            for feria in ferias_func:
                if (
                    feria["inicio"] <= sabado <= feria["fim"]
                    or feria["inicio"] <= domingo <= feria["fim"]
                ):
                    em_ferias = True
                    break

            if not em_ferias:
                distribuicao[func.id] = (sabado, domingo)
                fins_de_semana_alocados[idx].append(func.id)
                alocado = True
                break

        # Se não conseguiu alocar (todos fins de semana conflitam com férias),
        # forçar alocação no primeiro fim de semana com vaga
        if not alocado:
            for idx, (sabado, domingo) in enumerate(fins_de_semana_disponiveis):
                if len(fins_de_semana_alocados[idx]) < max_por_fds:
                    distribuicao[func.id] = (sabado, domingo)
                    fins_de_semana_alocados[idx].append(func.id)
                    break

    return distribuicao


def gerar_folgas_funcionario(
    funcionario,
    primeiro_dia,
    ultimo_dia,
    dias_bloqueados,
    ferias,
    fim_de_semana_atribuido=None,
):
    """
    Gera folgas para um funcionário específico
    """
    folgas = []

    # Mapear preferência para número de dia da semana
    preferencia_map = {
        "domingo": 6,
        "segunda": 0,
        "terca": 1,
        "quarta": 2,
        "quinta": 3,
        "sexta": 4,
        "sabado": 5,
    }

    dia_preferencia = preferencia_map.get(funcionario.preferencia_folga)

    # Encontrar todas as semanas do mês
    data_atual = primeiro_dia
    semanas = []
    semana_atual = []

    while data_atual <= ultimo_dia:
        semana_atual.append(data_atual)

        # Se é domingo (final da semana), iniciar nova semana
        if data_atual.weekday() == 6:
            semanas.append(semana_atual)
            semana_atual = []

        data_atual += timedelta(days=1)

    # Adicionar última semana se não estiver vazia
    if semana_atual:
        semanas.append(semana_atual)

    # Adicionar fim de semana completo atribuído (se houver)
    if fim_de_semana_atribuido:
        sabado, domingo = fim_de_semana_atribuido

        # Verificar se não estão em férias
        if not esta_em_ferias(sabado, ferias) and not esta_em_ferias(domingo, ferias):
            folgas.append({"funcionario_id": funcionario.id, "data": sabado})
            folgas.append({"funcionario_id": funcionario.id, "data": domingo})

    # Adicionar uma folga por semana (considerando preferência)
    for semana in semanas:
        # Pular semana se já tem fim de semana completo folgado
        tem_folga_na_semana = False
        for dia in semana:
            if any(f["data"] == dia for f in folgas):
                tem_folga_na_semana = True
                break

        if tem_folga_na_semana:
            continue

        # Tentar dia de preferência primeiro
        folga_adicionada = False

        if dia_preferencia is not None:
            # Verificar se o dia de preferência existe nesta semana
            dias_da_preferencia = [d for d in semana if d.weekday() == dia_preferencia]

            for dia in dias_da_preferencia:
                if dia not in dias_bloqueados and not esta_em_ferias(dia, ferias):
                    folgas.append({"funcionario_id": funcionario.id, "data": dia})
                    folga_adicionada = True
                    break

        # Se não conseguiu pelo dia de preferência ou se o dia de preferência não existe nesta semana,
        # só adicionar folga se houver dia bloqueado na semana
        if not folga_adicionada:
            # Verificar se tem algum dia bloqueado nesta semana
            tem_bloqueado_na_semana = any(dia in dias_bloqueados for dia in semana)

            if tem_bloqueado_na_semana:
                # Se tem dia bloqueado, dar folga em outro dia da semana
                for dia in semana:
                    if (
                        dia not in dias_bloqueados
                        and not esta_em_ferias(dia, ferias)
                        and not any(f["data"] == dia for f in folgas)
                    ):
                        folgas.append({"funcionario_id": funcionario.id, "data": dia})
                        break

    return folgas


def esta_em_ferias(data, ferias):
    """
    Verifica se uma data está dentro de um período de férias
    """
    for feria in ferias:
        if feria["inicio"] <= data <= feria["fim"]:
            return True
    return False


def _calcular_prioridade_faixas(faixas, data, eh_fds):
    """
    Calcula prioridade das faixas baseada na cobertura recebida de outras faixas.
    Faixas que recebem MENOS cobertura de outras têm MAIOR prioridade.
    Retorna lista de tuplas (faixa, prioridade) ordenada por prioridade (menor número = mais prioritária).
    """
    from datetime import time

    def str_to_minutes(hora_str):
        """Converte hora em string para minutos desde meia-noite"""
        h, m = hora_str.split(":")
        minutos = int(h) * 60 + int(m)
        # Apenas horários de madrugada (01:00-05:00) são considerados do dia seguinte
        # Para detectar, verificar se é menor que 6h (360 minutos) E se há faixas que terminam tarde
        # Solução mais simples: apenas 01:00 deve ser ajustado (horário que cruza meia-noite)
        if minutos < 120:  # Apenas 00:00 e 01:00 (menos de 2h = madrugada)
            minutos += 24 * 60
        return minutos

    faixas_ativas = [
        f for f in faixas if (eh_fds and f.ativo_fds) or (not eh_fds and f.ativo_semana)
    ]

    prioridades = []

    for faixa in faixas_ativas:
        inicio_faixa = str_to_minutes(faixa.hora_inicio)
        fim_faixa = str_to_minutes(faixa.hora_fim)
        duracao_faixa = fim_faixa - inicio_faixa

        # Calcular quanto desta faixa é coberto POR OUTRAS faixas (considerando união)
        minutos_faixa = set(range(inicio_faixa, fim_faixa))
        minutos_cobertos_por_outras = set()

        for outra_faixa in faixas_ativas:
            if outra_faixa.id == faixa.id:
                continue

            inicio_outra = str_to_minutes(outra_faixa.hora_inicio)
            fim_outra = str_to_minutes(outra_faixa.hora_fim)
            minutos_outra = set(range(inicio_outra, fim_outra))

            # Adicionar à cobertura apenas os minutos que fazem parte DA FAIXA ATUAL
            minutos_cobertos_por_outras.update(minutos_faixa & minutos_outra)

        # Calcular percentual da faixa que é coberto por outras
        if duracao_faixa > 0:
            percentual_coberto = (
                len(minutos_cobertos_por_outras) / duracao_faixa
            ) * 90  # Ajuste de escala para 0-90%
        else:
            percentual_coberto = 0

        # Prioridade: quanto MENOS coberto por outras, MENOR o número (mais prioritária)
        # 0% coberto = prioridade 0 (máxima), 100% coberto = prioridade 100 (mínima)
        prioridade = percentual_coberto

        prioridades.append((faixa, prioridade, percentual_coberto))

    # Ordenar por prioridade (menor número = mais importante = menos coberto)
    prioridades.sort(key=lambda x: x[1])

    return [(f, p) for f, p, _ in prioridades]


def gerar_escalas_com_faixas_horario(admin_id, ano, mes):
    """
    Gera escalas diárias alocando funcionários nas faixas de horário.
    Prioriza faixas menos cobertas por sobreposição.
    """
    # Buscar faixas de horário do admin
    faixas = (
        FaixaHorario.query.filter_by(admin_id=admin_id, ativo=True)
        .order_by(FaixaHorario.ordem)
        .all()
    )

    if not faixas:
        raise Exception("Nenhuma faixa de horário cadastrada")

    # Buscar funcionários ativos
    funcionarios = Funcionario.query.filter_by(admin_id=admin_id, ativo=True).all()

    if not funcionarios:
        raise Exception("Nenhum funcionário cadastrado")

    # Calcular período
    primeiro_dia = datetime(ano, mes, 12).date()
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano
    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    # Apagar escalas diárias existentes do período
    # Buscar IDs das escalas para deletar (não pode usar delete com join)
    escalas_para_deletar = (
        db.session.query(EscalaDiaria.id)
        .join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            EscalaDiaria.data >= primeiro_dia,
            EscalaDiaria.data <= ultimo_dia,
        )
        .all()
    )

    if escalas_para_deletar:
        ids_para_deletar = [e.id for e in escalas_para_deletar]
        EscalaDiaria.query.filter(EscalaDiaria.id.in_(ids_para_deletar)).delete(
            synchronize_session=False
        )

    db.session.commit()

    # Gerar folgas automaticamente antes de criar as escalas
    # Apagar folgas existentes do período
    folgas_existentes = (
        Folga.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            Folga.data >= primeiro_dia,
            Folga.data <= ultimo_dia,
        )
        .all()
    )

    for folga in folgas_existentes:
        db.session.delete(folga)

    db.session.commit()

    # Buscar dias bloqueados
    dias_bloqueados = DiaBloqueado.query.filter(
        DiaBloqueado.admin_id == admin_id,
        DiaBloqueado.data >= primeiro_dia,
        DiaBloqueado.data <= ultimo_dia,
    ).all()

    dias_bloqueados_set = set(db.data for db in dias_bloqueados)

    # Buscar férias para geração de folgas
    ferias_para_folgas = (
        Ferias.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            Ferias.data_fim >= primeiro_dia,
            Ferias.data_inicio <= ultimo_dia,
        )
        .all()
    )

    # Criar dicionário de férias por funcionário para geração de folgas
    ferias_por_funcionario = {}
    for feria in ferias_para_folgas:
        if feria.funcionario_id not in ferias_por_funcionario:
            ferias_por_funcionario[feria.funcionario_id] = []
        ferias_por_funcionario[feria.funcionario_id].append(
            {"inicio": feria.data_inicio, "fim": feria.data_fim}
        )

    # Coletar fins de semana disponíveis
    fins_de_semana_disponiveis = coletar_fins_de_semana(
        primeiro_dia, ultimo_dia, dias_bloqueados_set
    )

    # Distribuir fins de semana entre funcionários
    fins_de_semana_por_funcionario = distribuir_fins_de_semana(
        funcionarios, fins_de_semana_disponiveis, ferias_por_funcionario
    )

    # Gerar folgas para cada funcionário
    for func in funcionarios:
        fim_de_semana_atribuido = fins_de_semana_por_funcionario.get(func.id)

        folgas_func = gerar_folgas_funcionario(
            func,
            primeiro_dia,
            ultimo_dia,
            dias_bloqueados_set,
            ferias_por_funcionario.get(func.id, []),
            fim_de_semana_atribuido,
        )

        # Salvar folgas no banco
        for folga_data in folgas_func:
            nova_folga = Folga(
                funcionario_id=folga_data["funcionario_id"],
                data=folga_data["data"],
            )
            db.session.add(nova_folga)

    db.session.commit()

    # Buscar folgas e férias do período
    folgas = (
        Folga.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            Folga.data >= primeiro_dia,
            Folga.data <= ultimo_dia,
        )
        .all()
    )

    ferias = (
        Ferias.query.join(Funcionario)
        .filter(
            Funcionario.admin_id == admin_id,
            Ferias.data_fim >= primeiro_dia,
            Ferias.data_inicio <= ultimo_dia,
        )
        .all()
    )

    # Criar dicionário de folgas por data e funcionário
    folgas_dict = {}
    for folga in folgas:
        data_str = folga.data.strftime("%Y-%m-%d")
        if data_str not in folgas_dict:
            folgas_dict[data_str] = []
        folgas_dict[data_str].append(folga.funcionario_id)

    # Criar dicionário de férias por funcionário
    ferias_dict = {}
    for feria in ferias:
        if feria.funcionario_id not in ferias_dict:
            ferias_dict[feria.funcionario_id] = []
        ferias_dict[feria.funcionario_id].append(
            {"inicio": feria.data_inicio, "fim": feria.data_fim}
        )

    # Para cada dia do período
    data_atual = primeiro_dia
    while data_atual <= ultimo_dia:
        data_str = data_atual.strftime("%Y-%m-%d")
        funcionarios_de_folga = folgas_dict.get(data_str, [])

        # Verificar se é fim de semana
        eh_fds = data_atual.weekday() in [5, 6]  # Sábado=5, Domingo=6

        # Calcular prioridade das faixas para este dia
        faixas_priorizadas = _calcular_prioridade_faixas(faixas, data_atual, eh_fds)
        arr = open("log.txt", "a")
        arr.write(f"Data: {data_atual} - Faixas priorizadas: {faixas_priorizadas}\n")
        arr.close()

        # Encontrar melhor alocação para este dia
        melhor_alocacao = _encontrar_melhor_alocacao_dia(
            faixas_priorizadas,
            funcionarios,
            funcionarios_de_folga,
            ferias_dict,
            data_atual,
            admin_id,
        )

        # Aplicar a melhor alocação
        for func_id, faixa in melhor_alocacao:
            escala = EscalaDiaria(
                funcionario_id=func_id,
                faixa_horario_id=faixa.id,
                data=data_atual,
            )
            db.session.add(escala)

        data_atual += timedelta(days=1)

    db.session.commit()

    return {
        "sucesso": True,
        "mensagem": "Escalas geradas com sucesso",
    }


def _encontrar_melhor_alocacao_dia(
    faixas_priorizadas,
    todos_funcionarios,
    funcionarios_de_folga,
    ferias_dict,
    data_atual,
    admin_id,
):
    """
    Gera todas as combinações possíveis de alocação para o dia e escolhe a melhor.
    Depois aloca funcionários restantes em faixas onde têm disponibilidade.
    Retorna lista de tuplas (funcionario_id, faixa).
    """
    # Buscar disponibilidades de todos os funcionários para todas as faixas
    disponibilidades_por_faixa = {}

    for faixa, prioridade in faixas_priorizadas:
        disponibilidades = (
            DisponibilidadeFuncionario.query.filter_by(faixa_horario_id=faixa.id)
            .join(Funcionario)
            .filter(Funcionario.ativo == True, Funcionario.admin_id == admin_id)
            .all()
        )

        funcionarios_disponiveis = []
        for disp in disponibilidades:
            func_id = disp.funcionario_id

            # Verificar se não está de folga
            if func_id in funcionarios_de_folga:
                continue

            # Verificar se não está de férias
            if func_id in ferias_dict:
                em_ferias = False
                for feria in ferias_dict[func_id]:
                    if feria["inicio"] <= data_atual <= feria["fim"]:
                        em_ferias = True
                        break
                if em_ferias:
                    continue

            funcionarios_disponiveis.append(func_id)

        disponibilidades_por_faixa[faixa] = funcionarios_disponiveis

    # Gerar todas as combinações possíveis
    combinacoes = _gerar_combinacoes_alocacao(
        faixas_priorizadas, disponibilidades_por_faixa
    )

    # Se não há combinações possíveis, retorna vazio
    if not combinacoes:
        return []

    # Avaliar cada combinação e escolher a melhor
    melhor_combinacao = None
    melhor_pontuacao = -1

    for combinacao in combinacoes:
        pontuacao = _avaliar_combinacao(combinacao, faixas_priorizadas, data_atual)
        arr = open("log.txt", "a")
        arr.write(
            f"Data: {data_atual} - Combinacao: {combinacao} - Pontuacao: {pontuacao}\n"
        )
        arr.close()

        if pontuacao > melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor_combinacao = combinacao

    if not melhor_combinacao:
        melhor_combinacao = []

    # Registrar funcionários já alocados
    funcionarios_alocados = set(func_id for func_id, _ in melhor_combinacao)

    # Encontrar funcionários disponíveis que sobraram
    funcionarios_disponiveis_restantes = []
    for func in todos_funcionarios:
        # Verificar se já está alocado
        if func.id in funcionarios_alocados:
            continue

        # Verificar se está de folga
        if func.id in funcionarios_de_folga:
            continue

        # Verificar se está de férias
        if func.id in ferias_dict:
            em_ferias = False
            for feria in ferias_dict[func.id]:
                if feria["inicio"] <= data_atual <= feria["fim"]:
                    em_ferias = True
                    break
            if em_ferias:
                continue

        funcionarios_disponiveis_restantes.append(func.id)

    # Adicionar funcionários restantes nas faixas onde têm disponibilidade
    permitir_multiplos_por_faixa = True  # manter 1 funcionário por faixa neste momento
    if permitir_multiplos_por_faixa:
        for func_id in funcionarios_disponiveis_restantes:
            for faixa, _ in faixas_priorizadas:
                # Verificar se este funcionário tem disponibilidade para esta faixa
                if func_id in disponibilidades_por_faixa.get(faixa, []):
                    # Alocar este funcionário nesta faixa
                    melhor_combinacao.append((func_id, faixa))
                    break  # Apenas 1 faixa por funcionário por dia

    return melhor_combinacao


def _gerar_combinacoes_alocacao(faixas_priorizadas, disponibilidades_por_faixa):
    """
    Gera todas as combinações válidas de alocação.
    Cada funcionário pode trabalhar no máximo 1 turno por dia.
    """

    def gerar_recursivo(index, alocacao_atual, funcionarios_usados):
        # Caso base: percorremos todas as faixas
        if index >= len(faixas_priorizadas):
            return [alocacao_atual[:]]  # Retorna cópia da alocação atual

        faixa, _ = faixas_priorizadas[index]
        funcionarios_disponiveis = disponibilidades_por_faixa.get(faixa, [])

        todas_combinacoes = []

        # Opção 1: Não alocar ninguém nesta faixa (deixar descoberta)
        todas_combinacoes.extend(
            gerar_recursivo(index + 1, alocacao_atual, funcionarios_usados)
        )

        # Opção 2: Alocar um funcionário disponível que ainda não foi usado
        for func_id in funcionarios_disponiveis:
            if func_id not in funcionarios_usados:
                nova_alocacao = alocacao_atual + [(func_id, faixa)]
                novos_usados = funcionarios_usados | {func_id}
                todas_combinacoes.extend(
                    gerar_recursivo(index + 1, nova_alocacao, novos_usados)
                )

        return todas_combinacoes

    # Gerar todas as combinações
    todas = gerar_recursivo(0, [], set())

    # Log de diagnóstico para conferir total gerado
    try:
        arr = open("log.txt", "a")
        arr.write(f"Total de combinacoes geradas: {len(todas)}\n")
        arr.close()
    except Exception:
        pass

    return todas


def _avaliar_combinacao(combinacao, faixas_priorizadas, data_atual):
    """
    Avalia uma combinação de alocação baseada em critérios:
    1. Cobertura das faixas mais críticas (maior peso)
    2. Número de turnos cobertos
    3. Penalidade por deixar faixas críticas descobertas
    4. Penalidade de -1000 por cada hora descoberta no setor
    """
    if not combinacao:
        return 0

    pontuacao = 0

    # Criar mapa de faixas alocadas
    faixas_alocadas = {faixa.id: True for _, faixa in combinacao}

    # Criar mapa de prioridades
    prioridade_map = {faixa.id: prioridade for faixa, prioridade in faixas_priorizadas}

    # Critério 1: PRIORITÁRIO - Cobertura das faixas mais críticas (menos cobertas por outras)
    # Faixas com baixa prioridade (menos cobertas) têm maior importância
    for faixa, prioridade in faixas_priorizadas:
        if faixa.id in faixas_alocadas:
            # Alocar faixa crítica vale MUITO
            # Prioridade 0 (100% crítica) = 10000 pontos
            # Prioridade 100 (0% crítica) = 0 pontos
            pontos_cobertura = (100 - prioridade) * 100
            pontuacao += pontos_cobertura
        else:
            # PENALIDADE FORTE por deixar faixa crítica descoberta
            # Faixa crítica descoberta = -5000 pontos
            penalidade = (100 - prioridade) * 50
            pontuacao -= penalidade

    # Critério 2: Bonus por número total de turnos cobertos (menos importante)
    pontuacao += len(combinacao) * 100

    # Critério 3: Penalidade por horas descobertas no setor
    eh_fds = data_atual.weekday() in [5, 6]  # Sábado=5, Domingo=6

    # Determinar horário de operação: semana 5h-1h, FDS 7h-1h
    hora_inicio = 7 if eh_fds else 5
    hora_fim = 1  # Próximo dia

    # Converter string de hora para minutos
    def str_to_minutes(hora_str):
        h, m = hora_str.split(":")
        minutos = int(h) * 60 + int(m)
        if minutos < 120:  # Apenas 00:00 e 01:00 (menos de 2h = madrugada)
            minutos += 24 * 60
        return minutos

    # Coletar todas as horas cobertas pelas faixas alocadas
    horas_cobertas = set()
    for func_id, faixa in combinacao:
        inicio = str_to_minutes(faixa.hora_inicio)
        fim = str_to_minutes(faixa.hora_fim)
        # Adicionar cada hora
        for minuto in range(inicio, fim, 60):  # A cada 60 minutos (cada hora)
            hora = (minuto // 60) % 24
            horas_cobertas.add(hora)

    # Verificar cada hora de operação
    for hora in range(hora_inicio, 24):  # Horas de operação até meia-noite
        if hora not in horas_cobertas:
            pontuacao -= 1000  # Penalidade de -1000 por hora descoberta

    # Verificar horas após meia-noite (até hora_fim)
    for hora in range(0, hora_fim + 1):
        if hora not in horas_cobertas:
            pontuacao -= 1000  # Penalidade de -1000 por hora descoberta

    return pontuacao


def realocar_horarios_por_folga(data, funcionario_id_folga, admin_id):
    """
    Quando um funcionário entra de folga, realoca os horários
    garantindo que todas as faixas fiquem cobertas
    """
    # Buscar escalas deste funcionário neste dia
    escalas = EscalaDiaria.query.filter_by(
        funcionario_id=funcionario_id_folga, data=data
    ).all()

    # Para cada escala (faixa de horário) que ele estava alocado
    for escala in escalas:
        faixa = escala.faixa_horario

        # Buscar funcionários disponíveis para esta faixa
        disponibilidades = (
            DisponibilidadeFuncionario.query.filter_by(faixa_horario_id=faixa.id)
            .join(Funcionario)
            .filter(
                Funcionario.ativo == True,
                Funcionario.admin_id == admin_id,
                Funcionario.id != funcionario_id_folga,
            )
            .all()
        )

        # Buscar folgas e férias deste dia
        folgas = (
            Folga.query.join(Funcionario)
            .filter(Funcionario.admin_id == admin_id, Folga.data == data)
            .all()
        )

        ferias = (
            Ferias.query.join(Funcionario)
            .filter(
                Funcionario.admin_id == admin_id,
                Ferias.data_inicio <= data,
                Ferias.data_fim >= data,
            )
            .all()
        )

        funcionarios_de_folga = [f.funcionario_id for f in folgas]
        funcionarios_de_ferias = [f.funcionario_id for f in ferias]
        funcionarios_indisponiveis = set(funcionarios_de_folga + funcionarios_de_ferias)

        # Buscar funcionários já alocados neste dia
        funcionarios_ja_alocados = set(
            [e.funcionario_id for e in EscalaDiaria.query.filter_by(data=data).all()]
        )

        # Encontrar substituto
        substituto = None
        for disp in disponibilidades:
            func_id = disp.funcionario_id
            if func_id not in funcionarios_indisponiveis:
                # Preferir alguém que já está trabalhando neste dia (remanejamento)
                if func_id in funcionarios_ja_alocados:
                    substituto = func_id
                    break

        # Se não encontrou ninguém já trabalhando, pegar qualquer disponível
        if not substituto:
            for disp in disponibilidades:
                func_id = disp.funcionario_id
                if func_id not in funcionarios_indisponiveis:
                    substituto = func_id
                    break

        # Atualizar escala
        if substituto:
            escala.funcionario_id = substituto
        else:
            # Se não encontrou ninguém, remover a escala (faixa ficará descoberta)
            db.session.delete(escala)

    db.session.commit()


def _horario_coberto_por_outras_faixas(data, faixa_vazia, todas_faixas):
    """
    Verifica se o período de uma faixa vazia está totalmente coberto por outras faixas.
    Retorna True se o período está coberto, False caso contrário.
    """
    from datetime import datetime, time

    # Converter strings de hora para objetos time
    def str_to_time(hora_str):
        h, m = hora_str.split(":")
        return time(int(h), int(m))

    inicio_vazio = str_to_time(faixa_vazia.hora_inicio)
    fim_vazio = str_to_time(faixa_vazia.hora_fim)

    # Buscar todas as escalas do dia (exceto da faixa vazia)
    escalas_dia = (
        EscalaDiaria.query.filter_by(data=data)
        .filter(EscalaDiaria.faixa_horario_id != faixa_vazia.id)
        .all()
    )

    if not escalas_dia:
        return False  # Não há outras faixas alocadas

    # Coletar todos os períodos cobertos
    periodos_cobertos = []
    for escala in escalas_dia:
        faixa = escala.faixa_horario
        inicio = str_to_time(faixa.hora_inicio)
        fim = str_to_time(faixa.hora_fim)
        periodos_cobertos.append((inicio, fim))

    # Ordenar períodos por hora de início
    periodos_cobertos.sort()

    # Verificar se os períodos cobrem completamente a faixa vazia
    # Considera que horários podem cruzar meia-noite (ex: 19:00-01:00)
    if fim_vazio < inicio_vazio:  # Faixa vazia cruza meia-noite
        # Precisa cobrir de inicio_vazio até 23:59:59 E de 00:00:00 até fim_vazio
        cobre_noite = False
        cobre_manha = False

        for inicio_c, fim_c in periodos_cobertos:
            if fim_c < inicio_c:  # Período coberto também cruza meia-noite
                if inicio_c <= inicio_vazio and fim_c >= fim_vazio:
                    return True  # Um único período cobre tudo
            else:  # Período coberto não cruza meia-noite
                if inicio_c <= inicio_vazio:
                    cobre_noite = True
                if fim_c >= fim_vazio:
                    cobre_manha = True

        return cobre_noite and cobre_manha

    else:  # Faixa vazia não cruza meia-noite
        cobertura_atual = None

        for inicio_c, fim_c in periodos_cobertos:
            # Verificar períodos que cruzam meia-noite (ex: 19:00-01:00 cobre 17:00-23:00)
            if fim_c < inicio_c:  # Período coberto cruza meia-noite
                # Exemplo: 19:00-01:00 cruza meia-noite
                # Verifica sobreposição com: 19:00-23:59 E 00:00-01:00
                
                # Verifica se a faixa vazia (17:00-23:00) sobrepõe com 19:00-23:59
                if inicio_c <= fim_vazio and fim_vazio > inicio_c:
                    if cobertura_atual is None:
                        cobertura_atual = fim_vazio  # 19:00 cobre até 23:59
                    else:
                        cobertura_atual = max(cobertura_atual, fim_vazio)
                
                # Verifica se a faixa vazia sobrepõe com 00:00-01:00 (apenas se faixa vazia encostar na meia-noite)
                if inicio_vazio < time(0, 0) or (inicio_vazio == time(0, 0) and fim_vazio > time(0, 0)):
                    # Faixa vazia começa em ou antes da meia-noite
                    if fim_c > time(0, 0):
                        if cobertura_atual is None:
                            cobertura_atual = fim_c
                        else:
                            cobertura_atual = max(cobertura_atual, fim_c)
                continue

            # Período coberto não cruza meia-noite
            # Verificar se este período se sobrepõe com a faixa vazia
            if fim_c < inicio_vazio or inicio_c > fim_vazio:
                continue  # Não há sobreposição

            # Há sobreposição - verificar se estende a cobertura
            if cobertura_atual is None:
                if inicio_c <= inicio_vazio:
                    cobertura_atual = fim_c
            else:
                # Se o novo período começa antes do fim da cobertura atual (sobreposição)
                if inicio_c <= cobertura_atual:
                    cobertura_atual = max(cobertura_atual, fim_c)

        # Verificar se a cobertura alcançou o fim da faixa vazia
        return cobertura_atual is not None and cobertura_atual >= fim_vazio


def verificar_alertas_escalas(admin_id, ano, mes):
    """
    Verifica e retorna lista de alertas para:
    1. Funcionários trabalhando mais de 6 dias seguidos
    2. Faixas de horário sem cobertura (considerando sobreposição)
    Retorna lista de dicionários com informações dos alertas.
    """
    # Calcular período
    primeiro_dia = datetime(ano, mes, 12).date()
    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano
    ultimo_dia = datetime(proximo_ano, proximo_mes, 11).date()

    alertas_lista = []

    # 1. Verificar excesso de dias consecutivos
    funcionarios = Funcionario.query.filter_by(admin_id=admin_id, ativo=True).all()

    for func in funcionarios:
        dias_consecutivos = 0
        max_consecutivos = 0
        data_inicio_sequencia = None

        data_atual = primeiro_dia
        while data_atual <= ultimo_dia:
            # Verificar se está trabalhando neste dia
            escalas = EscalaDiaria.query.filter_by(
                funcionario_id=func.id, data=data_atual
            ).first()

            # Verificar se está de folga ou férias
            folga = Folga.query.filter_by(
                funcionario_id=func.id, data=data_atual
            ).first()

            ferias = Ferias.query.filter(
                Ferias.funcionario_id == func.id,
                Ferias.data_inicio <= data_atual,
                Ferias.data_fim >= data_atual,
            ).first()

            if escalas and not folga and not ferias:
                # Está trabalhando
                if dias_consecutivos == 0:
                    data_inicio_sequencia = data_atual
                dias_consecutivos += 1
                if dias_consecutivos > max_consecutivos:
                    max_consecutivos = dias_consecutivos
            else:
                # Não está trabalhando
                if dias_consecutivos > 6:
                    # Adicionar alerta à lista
                    alertas_lista.append(
                        {
                            "tipo": "excesso_dias",
                            "severidade": "alerta",
                            "mensagem": f'{func.nome} trabalhou {dias_consecutivos} dias consecutivos (de {data_inicio_sequencia.strftime("%d/%m")} a {(data_atual - timedelta(days=1)).strftime("%d/%m")})',
                            "data_referencia": data_inicio_sequencia,
                            "funcionario_id": func.id,
                            "funcionario_nome": func.nome,
                        }
                    )

                dias_consecutivos = 0

            data_atual += timedelta(days=1)

        # Verificar se terminou com sequência longa
        if dias_consecutivos > 6:
            alertas_lista.append(
                {
                    "tipo": "excesso_dias",
                    "severidade": "alerta",
                    "mensagem": f'{func.nome} trabalhou {dias_consecutivos} dias consecutivos (de {data_inicio_sequencia.strftime("%d/%m")} a {ultimo_dia.strftime("%d/%m")})',
                    "data_referencia": data_inicio_sequencia,
                    "funcionario_id": func.id,
                    "funcionario_nome": func.nome,
                }
            )

    # 2. Verificar falta de cobertura
    faixas = FaixaHorario.query.filter_by(admin_id=admin_id, ativo=True).all()

    data_atual = primeiro_dia
    while data_atual <= ultimo_dia:
        # Verificar se é fim de semana (sábado=5, domingo=6)
        eh_fds = data_atual.weekday() in [5, 6]

        for faixa in faixas:
            # Verificar se faixa está ativa neste tipo de dia
            if eh_fds and not faixa.ativo_fds:
                continue
            if not eh_fds and not faixa.ativo_semana:
                continue

            # Verificar se há funcionários disponíveis para esta faixa
            funcionarios_disponiveis = (
                DisponibilidadeFuncionario.query.filter_by(faixa_horario_id=faixa.id)
                .join(Funcionario)
                .filter(Funcionario.ativo == True)
                .count()
            )

            # Se não há nenhum funcionário disponível para esta faixa, não gerar alerta
            #if funcionarios_disponiveis == 0:
            #    continue    # Gerar alerta

            # Verificar se há alguém alocado
            escala = EscalaDiaria.query.filter_by(
                faixa_horario_id=faixa.id, data=data_atual
            ).first()

            if not escala:
                # Verificar se o horário está coberto por outras faixas
                if _horario_coberto_por_outras_faixas(data_atual, faixa, faixas):
                    continue  # Está coberto, não gerar alerta

                # Sem cobertura e não está coberto por outras faixas!
                tipo_dia = "fim de semana" if eh_fds else "dia de semana"
                alertas_lista.append(
                    {
                        "tipo": "sem_cobertura",
                        "severidade": "critico",
                        "mensagem": f'Faixa {faixa.hora_inicio}-{faixa.hora_fim} sem cobertura no dia {data_atual.strftime("%d/%m/%Y")} ({tipo_dia})',
                        "data_referencia": data_atual,
                        "faixa_horario_id": faixa.id,
                        "faixa_hora_inicio": faixa.hora_inicio,
                        "faixa_hora_fim": faixa.hora_fim,
                    }
                )

        data_atual += timedelta(days=1)

    return alertas_lista
