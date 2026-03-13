import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"


def search_congressman(name):
    """Search for the congressman by the name on the list received by the API"""

    response = requests.get(f"{BASE_URL}/deputados", params={
        "ordem": "ASC",
        "ordenarPor": "nome",
        "nome": name
    })

    congressman = response.json()

    return congressman["dados"]


def get_congressman(congressman_id):
    """This function receives the id of a congressman and returns the complete details"""

    response = requests.get(f"{BASE_URL}/deputados/{congressman_id}")

    congressman = response.json()

    return congressman["dados"]


def get_recent_votes():
    """Fetches recent Plenario votes with nominal voting records."""
    
    all_plen_votes = []
    page = 1
    
    while len(all_plen_votes) < 200 and page <= 20:
        response = requests.get(f"{BASE_URL}/votacoes", params={
            "itens": 100,
            "ordem": "DESC",
            "ordenarPor": "dataHoraRegistro",
            "pagina": page,
            "dataInicio": "2025-01-01"
        })
        
        data = response.json()
        
        if not data.get("dados"):
            break
            
        plen = [v for v in data["dados"] if v["siglaOrgao"] == "PLEN"]
        all_plen_votes.extend(plen)
        page += 1
        
    return all_plen_votes[:50]


def get_vote_details(vote_id):
    """Returns a list of all votes registered for a specific voting session.
    Note: absent congressmen are not listed."""

    response = requests.get(f"{BASE_URL}/votacoes/{vote_id}/votos")

    vote_details = response.json()

    return vote_details["dados"]


def get_propositions(congressman_id):   
    """This function receives the id of a congressman and returns the last 100 propositions of it"""

    response = requests.get(f"{BASE_URL}/proposicoes", params={
        "idDeputadoAutor": congressman_id,
        "itens": 100,
        "ordem": "DESC",
        "ordenarPor": "id"
    })

    propositions = response.json()

    return propositions["dados"]


def get_proposition(proposition_id):
    """This function receives the id of a proposition and returns the details of it"""

    response = requests.get(f"{BASE_URL}/proposicoes/{proposition_id}")

    proposition = response.json()

    return proposition["dados"]


def get_vote_orientation(vote_id):
    """This function receives the id of a vote and returns the orientation of the party"""

    response = requests.get(f"{BASE_URL}/votacoes/{vote_id}/orientacoes")

    vote_orientation = response.json()

    return vote_orientation["dados"]

