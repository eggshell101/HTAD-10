import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


BASE_URL = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils/"
)


def search_pubmed(
    query: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:

    query = query.strip()

    if not query:
        return []

    # =========================================================
    # 1. PUBMED ESEARCH
    # =========================================================

    search_url = BASE_URL + "esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": limit,
        "sort": "pub_date",
    }

    response = requests.get(
        search_url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    result = data.get(
        "esearchresult",
        {}
    )

    pmids = result.get(
        "idlist",
        []
    )

    if not pmids:
        return []

    # =========================================================
    # 2. PUBMED EFETCH
    # =========================================================

    fetch_url = BASE_URL + "efetch.fcgi"

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }

    response = requests.get(
        fetch_url,
        params=fetch_params,
        timeout=30,
    )

    response.raise_for_status()

    root = ET.fromstring(
        response.text
    )

    results = []

    for article in root.findall(
        ".//PubmedArticle"
    ):

        # -----------------------------------------------------
        # PMID
        # -----------------------------------------------------

        pmid_element = article.find(
            ".//PMID"
        )

        pmid = (
            pmid_element.text
            if pmid_element is not None
            else None
        )

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

        title_element = article.find(
            ".//ArticleTitle"
        )

        if title_element is not None:
            title = "".join(
                title_element.itertext()
            )
        else:
            title = ""

        # -----------------------------------------------------
        # ABSTRACT
        # -----------------------------------------------------

        abstract_parts = []

        for element in article.findall(
            ".//AbstractText"
        ):

            text = "".join(
                element.itertext()
            )

            if text:
                abstract_parts.append(text)

        abstract = " ".join(
            abstract_parts
        )

        # -----------------------------------------------------
        # PUBLICATION DATE
        # -----------------------------------------------------

        year = None
        month = None
        day = None

        pub_date = article.find(
            ".//PubDate"
        )

        if pub_date is not None:

            year_element = pub_date.find(
                "Year"
            )

            month_element = pub_date.find(
                "Month"
            )

            day_element = pub_date.find(
                "Day"
            )

            if year_element is not None:
                year = year_element.text

            if month_element is not None:
                month = month_element.text

            if day_element is not None:
                day = day_element.text

        if year:
            date_value = str(year)

            if month:
                date_value += f"-{month}"

            if day:
                date_value += f"-{day}"

        else:
            date_value = None

        results.append(
            {
                "source": "PubMed",
                "title": title,
                "date": date_value,
                "abstract": abstract,
                "identifier": pmid,
                "url": (
                    f"https://pubmed.ncbi.nlm.nih.gov/"
                    f"{pmid}/"
                    if pmid
                    else None
                ),
            }
        )

    return results