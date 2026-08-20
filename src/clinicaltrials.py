import requests
from typing import List, Dict, Any


BASE_URL = (
    "https://clinicaltrials.gov/"
    "api/v2/studies"
)


def fetch_trials(
    query: str,
    page_size: int = 20,
) -> List[Dict[str, Any]]:

    query = query.strip()

    if not query:
        return []

    params = {
        "query.term": query,
        "pageSize": page_size,
        "format": "json",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    studies = payload.get(
        "studies",
        []
    )

    results = []

    for study in studies:

        protocol = study.get(
            "protocolSection",
            {}
        )

        identification = protocol.get(
            "identificationModule",
            {}
        )

        status = protocol.get(
            "statusModule",
            {}
        )

        identification_id = (
            identification.get(
                "nctId"
            )
        )

        title = (
            identification.get(
                "briefTitle"
            )
            or identification.get(
                "officialTitle"
            )
            or ""
        )

        date_value = (
            status.get(
                "studyFirstPostDateStruct",
                {}
            ).get("date")
        )

        results.append(
            {
                "source": "ClinicalTrials.gov",
                "title": title,
                "date": date_value,
                "abstract": "",
                "identifier": identification_id,
                "url": (
                    f"https://clinicaltrials.gov/"
                    f"study/{identification_id}"
                    if identification_id
                    else None
                ),
                "raw": study,
            }
        )

    return results