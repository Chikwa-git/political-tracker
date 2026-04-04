import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
REQUEST_TIMEOUT = 30


def _get_json(endpoint, params=None):
    """Perform an API GET with timeout and HTTP status validation."""

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def search_congressman(name):
    """Search for the congressman by the name on the list received by the API"""

    congressman = _get_json("deputados", params={
        "ordem": "ASC",
        "ordenarPor": "nome",
        "nome": name
    })

    return congressman["dados"]


def get_congressman(congressman_id):
    """This function receives the id of a congressman and returns the complete details"""

    congressman = _get_json(f"deputados/{congressman_id}")

    return congressman["dados"]


def get_recent_votes():
    """Fetches recent Plenario votes with nominal voting records."""
    
    all_plen_votes = []
    page = 1
    
    while len(all_plen_votes) < 200 and page <= 20:
        data = _get_json("votacoes", params={
            "itens": 100,
            "ordem": "DESC",
            "ordenarPor": "dataHoraRegistro",
            "pagina": page,
            "dataInicio": "2025-01-01"
        })
        
        if not data.get("dados"):
            break
            
        plen = [v for v in data["dados"] if v["siglaOrgao"] == "PLEN"]
        all_plen_votes.extend(plen)
        page += 1
        
    return all_plen_votes[:50]


def get_vote_details(vote_id):
    """Returns a list of all votes registered for a specific voting session.
    Note: absent congressmen are not listed."""

    vote_details = _get_json(f"votacoes/{vote_id}/votos")

    return vote_details["dados"]


def get_propositions(congressman_id):   
    """This function receives the id of a congressman and returns the last 100 propositions of it"""

    propositions = _get_json("proposicoes", params={
        "idDeputadoAutor": congressman_id,
        "itens": 100,
        "ordem": "DESC",
        "ordenarPor": "id"
    })

    return propositions["dados"]


def get_proposition(proposition_id):
    """This function receives the id of a proposition and returns the details of it"""

    proposition = _get_json(f"proposicoes/{proposition_id}")

    return proposition["dados"]


def get_vote_orientation(vote_id):
    """This function receives the id of a vote and returns the orientation of the party"""

    vote_orientation = _get_json(f"votacoes/{vote_id}/orientacoes")

    return vote_orientation["dados"]

