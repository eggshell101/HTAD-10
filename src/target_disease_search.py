import requests


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_pubmed(target, disease, retmax=5):

    query = f'"{target}" AND "{disease}"'

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": retmax,
    }

    response = requests.get(
        f"{BASE_URL}/esearch.fcgi",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["esearchresult"]["idlist"]