import csv
import json
import re
from pathlib import Path
from typing import Optional, Dict
import requests

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DRUG_FILE = DATA_DIR / "drugs.csv"
DISEASE_FILE = DATA_DIR / "diseases.csv"
CACHE_FILE = DATA_DIR / "entity_cache.json"


def lookup_drug_online(query: str):
    """
    Look up a drug/chemical using PubChem.
    Returns a normalized entity dictionary or None.
    """

    if not query:
        return None

    url = (
        "https://pubchem.ncbi.nlm.nih.gov/"
        "rest/pug/compound/name/"
        f"{requests.utils.quote(query)}"
        "/property/Title,CanonicalSMILES,IsomericSMILES,"
        "MolecularFormula,MolecularWeight/JSON"
    )

    try:

        response = requests.get(
            url,
            timeout=15,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        properties = (
            data
            .get("PropertyTable", {})
            .get("Properties", [])
        )

        if not properties:
            return None

        prop = properties[0]

        canonical = (
            prop.get("Title")
            or query
        )

        return {
            "canonical_name": canonical,
            "synonyms": [query],
            "drug_type": "chemical",
            "source": "online",
            "pubchem_cid": prop.get("CID"),
            "molecular_formula": prop.get(
                "MolecularFormula"
            ),
            "molecular_weight": prop.get(
                "MolecularWeight"
            ),
            "canonical_smiles": prop.get(
                "ConnectivitySMILES"
            ) or prop.get(
                "CanonicalSMILES"
            ),
        }

    except Exception as exc:

        print(
            "[ENTITY LOOKUP WARNING]",
            exc,
        )

        return None

    
def lookup_disease_online(query: str):
    """
    Look up a disease using Disease Ontology and select
    the best semantic/lexical match instead of blindly
    taking the first result.
    """

    if not query:
        return None

    url = "https://api.disease-ontology.org/v1/terms/search"

    payload = {
        "data": {
            "names": [query]
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        if response.status_code != 200:
            print(
                "[DISEASE LOOKUP]",
                response.status_code,
            )
            return None

        data = response.json()

        terms = (
            data.get("data")
            or data.get("terms")
            or data.get("results")
            or []
        )

        if isinstance(terms, dict):
            terms = (
                terms.get("items")
                or terms.get("results")
                or []
            )

        if not terms:
            return None

        q = normalize(query)

        best = None
        best_score = 0

        for result in terms:

            canonical = (
                result.get("name")
                or result.get("label")
                or result.get("term")
                or ""
            )

            if not canonical:
                continue

            canonical_norm = normalize(
                canonical
            )

            score = 0

            # Exact canonical match
            if canonical_norm == q:
                score = 100

            # Query contained in canonical name
            elif q in canonical_norm:
                score = 80

            # Canonical contained in query
            elif canonical_norm in q:
                score = 70

            # Check synonyms
            raw_synonyms = (
                result.get("synonyms")
                or result.get("synonym")
                or []
            )

            if isinstance(
                raw_synonyms,
                str,
            ):
                raw_synonyms = [
                    raw_synonyms
                ]

            for synonym in raw_synonyms:

                if isinstance(
                    synonym,
                    dict,
                ):
                    synonym = (
                        synonym.get("name")
                        or synonym.get("label")
                        or synonym.get("value")
                        or ""
                    )

                synonym_norm = normalize(
                    str(synonym)
                )

                if synonym_norm == q:
                    score = max(
                        score,
                        95,
                    )

                elif q in synonym_norm:
                    score = max(
                        score,
                        75,
                    )

            if score > best_score:

                best_score = score
                best = result

        # Reject weak matches
        if best is None or best_score < 70:
            return None

        canonical = (
            best.get("name")
            or best.get("label")
            or best.get("term")
        )

        synonyms = []

        raw_synonyms = (
            best.get("synonyms")
            or best.get("synonym")
            or []
        )

        if isinstance(
            raw_synonyms,
            str,
        ):
            raw_synonyms = [
                raw_synonyms
            ]

        for synonym in raw_synonyms:

            if isinstance(
                synonym,
                dict,
            ):
                synonym = (
                    synonym.get("name")
                    or synonym.get("label")
                    or synonym.get("value")
                )

            if synonym:
                synonyms.append(
                    str(synonym)
                )

        if query not in synonyms:
            synonyms.append(query)

        disease_id = (
            best.get("id")
            or best.get("doid")
            or best.get("DOID")
        )

        return {
            "canonical_name": canonical,
            "synonyms": synonyms,
            "drug_type": None,
            "source": "online",
            "disease_id": disease_id,
            "definition": best.get(
                "definition"
            ),
            "match_score": best_score,
        }

    except Exception as exc:

        print(
            "[DISEASE LOOKUP WARNING]",
            exc,
        )

        return None

    
def lookup_disease_mesh(query: str):
    """
    Fallback disease lookup using NLM MeSH.
    """

    if not query:
        return None

    url = (
        "https://id.nlm.nih.gov/mesh/"
        "lookup/descriptor"
    )

    params = {
        "label": query,
        "match": "exact",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers={
                "Accept": "application/json"
            },
            timeout=15,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data:
            return None

        result = data[0]

        return {
            "canonical_name": query,
            "synonyms": [query],
            "drug_type": None,
            "source": "mesh",
            "mesh_uri": result,
        }

    except Exception as exc:

        print(
            "[MESH LOOKUP WARNING]",
            exc,
        )

        return None
    
def normalize(text: str) -> str:
    """
    Normalize an entity name for matching.
    """

    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(
        r"[^a-z0-9\s\-]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _load_csv(path: Path) -> Dict[str, dict]:

    entities = {}

    if not path.exists():
        return entities

    with open(
        path,
        "r",
        encoding="utf-8",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            canonical = (
                row.get("canonical_name")
                or ""
            ).strip()

            if not canonical:
                continue

            canonical_norm = normalize(
                canonical
            )

            entities[canonical_norm] = {
                "canonical_name": canonical,
                "synonyms": [],
                "drug_type": row.get(
                    "drug_type"
                ),
            }

            synonyms = (
                row.get("synonyms")
                or ""
            )

            for synonym in synonyms.split("|"):

                synonym = synonym.strip()

                if synonym:
                    entities[
                        canonical_norm
                    ]["synonyms"].append(
                        synonym
                    )

    return entities


def _load_cache() -> dict:

    if not CACHE_FILE.exists():
        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def _save_cache(cache: dict):

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            cache,
            f,
            indent=2,
            ensure_ascii=False,
        )


def _match_local(
    query: str,
    entities: Dict[str, dict],
) -> Optional[dict]:

    q = normalize(query)

    if not q:
        return None

    # Exact canonical name
    if q in entities:

        result = dict(
            entities[q]
        )

        result["source"] = "local"

        return result

    # Synonym matching
        # Safe partial matching
    for key, entity in entities.items():

        candidates = [
            entity.get("canonical_name", ""),
            *entity.get("synonyms", []),
        ]

        for candidate in candidates:

            candidate_norm = normalize(candidate)

            if (
                q in candidate_norm
                or candidate_norm in q
            ):

                result = dict(entity)
                result["source"] = "local"

                return result

    return None

def resolve_drug(
    query: str,
) -> Optional[dict]:

    if not query:
        return None

    # ========================================================
    # 1. LOCAL CSV
    # ========================================================

    entities = _load_csv(
        DRUG_FILE
    )

    result = _match_local(
        query,
        entities,
    )

    if result:
        return result

    # ========================================================
    # 2. CACHE
    # ========================================================

    cache = _load_cache()

    cache_key = (
        f"drug:{normalize(query)}"
    )

    cached = cache.get(
        cache_key
    )

    if cached:

        cached["source"] = "cache"

        return cached

    # ========================================================
    # 3. ONLINE PUBCHEM
    # ========================================================

    result = lookup_drug_online(
        query
    )

    if result:

        # Cache the successful lookup
        cache[cache_key] = result

        _save_cache(
            cache
        )

        return result

    # ========================================================
    # 4. UNKNOWN
    # ========================================================

    return None


def resolve_disease(
    query: str,
) -> Optional[dict]:

    if not query:
        return None

    # ========================================================
    # 1. LOCAL CSV
    # ========================================================

    entities = _load_csv(
        DISEASE_FILE
    )

    result = _match_local(
        query,
        entities,
    )

    if result:
        return result

    # ========================================================
    # 2. CACHE
    # ========================================================

    cache = _load_cache()

    cache_key = (
        f"disease:{normalize(query)}"
    )

    cached = cache.get(
        cache_key
    )

    if cached:

        cached["source"] = "cache"

        return cached

    # ========================================================
    # 3. DISEASE ONTOLOGY
    # ========================================================

    result = lookup_disease_online(
        query
    )

    # ========================================================
    # 4. MESH FALLBACK
    # ========================================================

    if not result:

        result = lookup_disease_mesh(
            query
        )

    # ========================================================
    # 5. CACHE
    # ========================================================

    if result:

        cache[cache_key] = result

        _save_cache(
            cache
        )

        return result

    return None


def cache_entity(
    entity_type: str,
    query: str,
    entity: dict,
):

    cache = _load_cache()

    key = (
        f"{entity_type}:"
        f"{normalize(query)}"
    )

    cache[key] = entity

    _save_cache(
        cache
    )   