import requests
from datetime import date, timedelta
from typing import List, Dict, Any


BASE_URL = "https://api.biorxiv.org/details"

HEADERS = {
    "User-Agent": "HTAD-10/1.0 biomedical-evidence-engine"
}


def fetch_preprints(
    server: str = "medrxiv",
    days: int = 30,
    cursor: int = 0,
) -> List[Dict[str, Any]]:

    if server not in {"biorxiv", "medrxiv"}:
        raise ValueError(
            "server must be 'biorxiv' or 'medrxiv'"
        )

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    url = (
        f"{BASE_URL}/{server}/"
        f"{start_date.isoformat()}/"
        f"{end_date.isoformat()}/"
        f"{cursor}"
    )

    print(
        f"[medRxiv] Requesting: {url}"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,

            # Separate connect/read timeout.
            # This prevents the program from hanging
            # indefinitely while downloading the response.
            timeout=(10, 20),

        )

        response.raise_for_status()

        payload = response.json()

    except requests.exceptions.Timeout:

        print(
            "[medRxiv] Request timed out. "
            "Skipping medRxiv."
        )

        return []

    except requests.exceptions.RequestException as exc:

        print(
            f"[medRxiv] Request failed: {exc}"
        )

        return []

    except ValueError as exc:

        print(
            f"[medRxiv] Invalid JSON response: {exc}"
        )

        return []

    results = []

    for item in payload.get(
        "collection",
        []
    ):

        doi = item.get("doi")

        results.append(
            {
                "source": "medRxiv",

                "title": item.get(
                    "title",
                    "",
                ),

                "date": item.get(
                    "date"
                ),

                "abstract": item.get(
                    "abstract",
                    "",
                ),

                "identifier": doi,

                "url": (
                    f"https://doi.org/{doi}"
                    if doi
                    else None
                ),
            }
        )

    print(
        f"[medRxiv] Retrieved "
        f"{len(results)} records."
    )

    return results


def search_preprints(
    query: str,
    server: str = "medrxiv",
    days: int = 30,
    max_results: int = 30,
) -> List[Dict[str, Any]]:

    query = (
        query
        .strip()
        .lower()
    )

    if not query:
        return []

    # --------------------------------------------------------
    # Split the search query into terms.
    #
    # Example:
    #
    # "Siponimod AND Alzheimer's"
    #
    # becomes:
    #
    # ["siponimod", "alzheimer's"]
    # --------------------------------------------------------

    query = query.replace(
        " AND ",
        " "
    )

    terms = [
        term.strip()
        for term in query.split()
        if term.strip()
    ]

    if not terms:
        return []

    results = []

    # --------------------------------------------------------
    # We only need a small number of pages.
    #
    # Do NOT continuously crawl medRxiv.
    # --------------------------------------------------------

    max_pages = 3

    for page in range(
        max_pages
    ):

        if len(results) >= max_results:
            break

        cursor = page * 30

        batch = fetch_preprints(
            server=server,
            days=days,
            cursor=cursor,
        )

        if not batch:
            break

        for paper in batch:

            text = (
                f"{paper.get('title', '')} "
                f"{paper.get('abstract', '')}"
            ).lower()

            # ------------------------------------------------
            # Match all query terms.
            # ------------------------------------------------

            if all(
                term in text
                for term in terms
            ):

                results.append(
                    paper
                )

            if len(results) >= max_results:
                break

    print(
        f"[medRxiv] Relevant results: "
        f"{len(results)}"
    )

    return results