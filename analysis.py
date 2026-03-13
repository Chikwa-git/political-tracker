# analysis.py
# NOTE: This file was initially generated with the assistance of Claude (Anthropic)
# as part of the CS50X final project development process.
# The logic was reviewed, studied and understood by the author.
# Reference: https://claude.ai

import camara


def get_congressman_history(congressman_id):
    """
    Returns the voting history of a congressman in the last 100 votes.
    Each item contains the vote_id, description, date, and the vote type.
    If the congressman was absent, the vote type is "Ausente".
    """

    history = []

    # Fetch the 100 recent votes from the Chamber
    recent_votes = camara.get_recent_votes()

    for vote in recent_votes:
        # Fetch individual votes for each vote session
        vote_details = camara.get_vote_details(vote["id"])

        if len(vote_details) < 50:
            continue

        # Iterate through votes looking for the congressman
        # Python's "for/else" works like this:
        # - If the loop ends with "break" → the "else" does NOT execute
        # - If the loop ends naturally → the "else" executes
        for voto in vote_details:
            if voto["deputado_"]["id"] == congressman_id:
                # Congressman found → record his/her vote
                history.append({
                    "vote_id": vote["id"],
                    "description": vote["descricao"],
                    "date": vote["data"],
                    "vote": voto["tipoVoto"]  # "Sim", "Não", "Abstenção", "Obstrução"
                })
                break  # Break the inner loop — already found the congressman
        else:
            # Congressman not found in any vote → was absent
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

    # Count how many votes the congressman was NOT absent
    present = sum(1 for item in history if item["vote"] != "Ausente")

    # Calculate the percentage
    # Ex: 87 present / 100 total * 100 = 87.0%
    return round((present / total) * 100, 1)


def get_majority_alignment(congressman_id):
    """
    Calculates the alignment percentage of a congressman with the Chamber majority.
    Returns a float between 0 and 100.
    More reliable than party alignment since "Maioria" always appears in orientations.
    """

    aligned = 0
    total = 0

    recent_votes = camara.get_recent_votes()

    for vote in recent_votes:
        vote_details = camara.get_vote_details(vote["id"])
        if len(vote_details) < 50:
            continue

        orientations = camara.get_vote_orientation(vote["id"])

        # Find the congressman's vote
        congressman_vote = None
        for voto in vote_details:
            if voto["deputado_"]["id"] == congressman_id:
                congressman_vote = voto["tipoVoto"]
                break

        if not congressman_vote:
            continue

        # Find the majority orientation
        majority_orientation = None
        for o in orientations:
            if o["siglaPartidoBloco"] == "Maioria" and o["orientacaoVoto"]:
                majority_orientation = o["orientacaoVoto"]
                break

        if not majority_orientation:
            continue

        total += 1
        if congressman_vote == majority_orientation:
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

    # Dictionary that will accumulate common votes between congressmen
    # Structure: { congressman_id: { "same": 0, "total": 0, "name": "...", "party": "..." } }
    comparisons = {}

    recent_votes = camara.get_recent_votes()

    for vote in recent_votes:
        vote_details = camara.get_vote_details(vote["id"])

        # Step 1 — find the main congressman's vote
        congressman_vote = None
        for voto in vote_details:
            if voto["deputado_"]["id"] == congressman_id:
                congressman_vote = voto["tipoVoto"]
                break

        # If was absent, skip this vote
        if congressman_vote is None:
            continue

        # Step 2 — compare with all other congressmen who voted
        for voto in vote_details:
            other_id = voto["deputado_"]["id"]

            # Don't compare with himself
            if other_id == congressman_id:
                continue

            # Initialize the congressman's record if it doesn't exist yet
            if other_id not in comparisons:
                comparisons[other_id] = {
                    "id": other_id,
                    "name": voto["deputado_"]["nome"],
                    "party": voto["deputado_"]["siglaPartido"],
                    "same": 0,    # same votes
                    "total": 0    # total votes in common
                }

            comparisons[other_id]["total"] += 1

            if voto["tipoVoto"] == congressman_vote:
                comparisons[other_id]["same"] += 1

    # Step 3 — calculate alignment % for each congressman
    alignments = []
    for other_id, data in comparisons.items():
        # Only consider congressmen with at least 10 votes in common
        # Avoids distortions from insufficient data
        if data["total"] < 10:
            continue

        alignment = round((data["same"] / data["total"]) * 100, 1)
        alignments.append({
            "id": other_id,
            "name": data["name"],
            "party": data["party"],
            "alignment": alignment
        })

    # Step 4 — sort and get top 5 from each extreme
    # sorted() with reverse=True → from largest to smallest
    alignments.sort(key=lambda x: x["alignment"], reverse=True)

    return {
        "most_aligned": alignments[:5],     # top 5 who vote the same
        "least_aligned": alignments[-5:]    # top 5 who vote differently
    }
