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
    """This function returns the 100 recent votes by the Chamber"""

    response = requests.get(f"{BASE_URL}/votacoes", params={
        "itens": 100,
        "ordem": "DESC",
        "ordenarPor": "dataHoraRegistro"
    })

    votes = response.json()

    return votes["dados"]


def get_vote_details(vote_id):
    """This function receives the id of a vote and returns the details of it"""

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


def get_blocks():
    """This function returns the blocks of the Chamber"""

    response = requests.get(f"{BASE_URL}/blocos")

    blocks = response.json()

    return blocks["dados"]


def get_block_parties(block_id):
    """This function returns the parties of the blocks of the Chamber"""

    response = requests.get(f"{BASE_URL}/blocos/{block_id}/partidos")

    block_parties = response.json()

    return block_parties["dados"]