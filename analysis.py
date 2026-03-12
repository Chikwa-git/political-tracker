import camara


def get_congressman_history(congressman_id):
    """
    Returns the voting history of a congressman in the last 100 votes.
    Each item contains the vote_id, description, date, and the vote type.
    If the congressman was absent, the vote type is "Ausente".
    """

    history = []

    # Busca as 100 votações recentes da Câmara
    recent_votes = camara.get_recent_votes()

    for vote in recent_votes:
        # Busca os votos individuais de cada votação
        vote_details = camara.get_vote_details(vote["id"])

        # Percorre os votos da votação procurando o deputado
        # O "for/else" do Python funciona assim:
        # - Se o loop terminar com "break" → o "else" NÃO executa
        # - Se o loop terminar naturalmente → o "else" executa
        for voto in vote_details:
            if voto["deputado_"]["id"] == congressman_id:
                # Deputado encontrado → registra o voto dele
                history.append({
                    "vote_id": vote["id"],
                    "description": vote["descricao"],
                    "date": vote["data"],
                    "vote": voto["tipoVoto"]  # "Sim", "Não", "Abstenção", "Obstrução"
                })
                break  # Para o loop interno — já encontrou o deputado
        else:
            # Deputado não encontrado em nenhum voto → estava ausente
            history.append({
                "vote_id": vote["id"],
                "description": vote["descricao"],
                "date": vote["data"],
                "vote": "Ausente"
            })

    return history


def get_presence_rate(history):
    """
    Calculates the presence rate of a congressman based on their voting history.
    Returns a float between 0 and 100 representing the percentage of presence.

    Receives the history returned by get_congressman_history().
    """

    total = len(history)

    if total == 0:
        return 0

    # Conta quantas votações o deputado NÃO foi ausente
    present = sum(1 for item in history if item["vote"] != "Ausente")

    # Calcula a porcentagem
    # Ex: 87 presentes / 100 total * 100 = 87.0%
    return round((present / total) * 100, 1)


def get_party_alignment(congressman_id, party):
    """
    Calculates the alignment percentage of a congressman with their party.
    Returns a float between 0 and 100.

    - Fetches recent votes
    - For each vote, checks the party orientation
    - Compares with the congressman's vote
    - If the party "liberated" the vote (empty orientation), that vote is ignored
    """

    aligned = 0      # votações onde o deputado seguiu o partido
    total = 0        # total de votações comparáveis (exclui ausências e bancada liberada)

    recent_votes = camara.get_recent_votes()

    for vote in recent_votes:
        vote_details = camara.get_vote_details(vote["id"])
        orientations = camara.get_vote_orientation(vote["id"])

        # Passo 1 — encontrar o voto do deputado nessa votação
        congressman_vote = None
        for voto in vote_details:
            if voto["deputado_"]["id"] == congressman_id:
                congressman_vote = voto["tipoVoto"]
                break

        # Se o deputado estava ausente, não conta para o alinhamento
        if congressman_vote is None:
            continue

        # Passo 2 — encontrar a orientação do partido do deputado
        # O campo codTipoLideranca = "P" significa que é um partido (não bloco)
        party_orientation = None
        for orientation in orientations:
            if orientation["siglaPartidoBloco"] == party and orientation["codTipoLideranca"] == "P":
                party_orientation = orientation["orientacaoVoto"]
                break

        # Se o partido liberou a bancada (orientação vazia) ou não orientou, ignora essa votação
        if not party_orientation:
            continue

        # Passo 3 — comparar o voto do deputado com a orientação do partido
        total += 1
        if congressman_vote == party_orientation:
            aligned += 1

    if total == 0:
        return 0

    return round((aligned / total) * 100, 1)


def get_political_alignment(congressman_id):
    """
    Returns the top 5 congressmen who vote most similarly and most differently
    from the given congressman, based on the last 100 votes.

    Returns a dict with two lists:
    {
        "most_aligned": [ {"id": ..., "name": ..., "party": ..., "alignment": ...}, ... ],
        "least_aligned": [ {"id": ..., "name": ..., "party": ..., "alignment": ...}, ... ]
    }
    """

    # Dicionário que vai acumular os votos em comum entre os deputados
    # Estrutura: { congressman_id: { "same": 0, "total": 0, "name": "...", "party": "..." } }
    comparisons = {}

    recent_votes = camara.get_recent_votes()

    for vote in recent_votes:
        vote_details = camara.get_vote_details(vote["id"])

        # Passo 1 — encontrar o voto do deputado principal
        congressman_vote = None
        for voto in vote_details:
            if voto["deputado_"]["id"] == congressman_id:
                congressman_vote = voto["tipoVoto"]
                break

        # Se estava ausente, pula essa votação
        if congressman_vote is None:
            continue

        # Passo 2 — comparar com todos os outros deputados que votaram
        for voto in vote_details:
            other_id = voto["deputado_"]["id"]

            # Não compara consigo mesmo
            if other_id == congressman_id:
                continue

            # Inicializa o registro do deputado se ainda não existe
            if other_id not in comparisons:
                comparisons[other_id] = {
                    "id": other_id,
                    "name": voto["deputado_"]["nome"],
                    "party": voto["deputado_"]["siglaPartido"],
                    "same": 0,    # votações iguais
                    "total": 0    # total de votações em comum
                }

            comparisons[other_id]["total"] += 1

            if voto["tipoVoto"] == congressman_vote:
                comparisons[other_id]["same"] += 1

    # Passo 3 — calcular o % de alinhamento de cada deputado
    alignments = []
    for other_id, data in comparisons.items():
        # Só considera deputados com pelo menos 10 votações em comum
        # Evita distorções por poucos dados
        if data["total"] < 10:
            continue

        alignment = round((data["same"] / data["total"]) * 100, 1)
        alignments.append({
            "id": other_id,
            "name": data["name"],
            "party": data["party"],
            "alignment": alignment
        })

    # Passo 4 — ordenar e pegar top 5 de cada extremo
    # sorted() com reverse=True → do maior pro menor
    alignments.sort(key=lambda x: x["alignment"], reverse=True)

    return {
        "most_aligned": alignments[:5],     # top 5 que mais votam igual
        "least_aligned": alignments[-5:]    # top 5 que mais votam diferente
    }
