from src.biorxiv import fetch_preprints
from src.clinicaltrials import fetch_trials
from src.signal_extractor import extract_signals
from src.cross_indication import detect_cross_indication
from src.evidence_graph import EvidenceGraph
from src.relationship_extractor import extract_relationships
from src.known_indications import KNOWN_INDICATIONS
from src.target_disease_search import search_pubmed



def main():

    print("=" * 60)
    print("HTAD-10 — Evidence Discovery Engine")
    print("=" * 60)

    print("\n[1] Fetching recent medRxiv papers...")

    papers = fetch_preprints(
        server="medrxiv",
        days=7
    )

    print(f"Retrieved {len(papers)} papers.")

    for paper in papers[:5]:

        print("\n---")
        print(paper.title)
        print("Date:", paper.date)
        print("DOI:", paper.identifier)

    print("\n[2] Searching ClinicalTrials.gov...")

    trials = fetch_trials(
        query="drug repurposing",
        page_size=10
    )

    print(f"Retrieved {len(trials)} trials.")

    for trial in trials[:5]:

        print("\n---")
        print(trial.title)
        print("Date:", trial.date)
        print("ID:", trial.identifier)


    print("\n[3] Detecting repurposing signals...")

    all_evidence = papers + trials

    signals = extract_signals(all_evidence)

    print(f"Detected {len(signals)} candidate signals.")

    for signal in signals:

        print("\n==============================")
        print("Drug:", signal.drug)
        print("Disease:", signal.disease)
        print("Target:", signal.target)

        for evidence in signal.evidence:
            print("Source:", evidence.source)
            print("Title:", evidence.title)

    print("\n[4] Extracting relationships...")

    all_relationships = []

    for evidence in all_evidence:

        relationships = extract_relationships(evidence)

        all_relationships.extend(relationships)


    print(
        f"Extracted {len(all_relationships)} relationships."
    )


    for relation in all_relationships:

        print("\n------------------------------")

        print("Type:", relation["type"])
        print("Drug:", relation["drug"])
        print("Target:", relation["target"])
        print("Disease:", relation["disease"])
        print(
            "Evidence:",
            relation["evidence"].title
        )
    """print("\n[4] Detecting cross-indication signals...")

    cross_indication_signals = []

    for signal in signals:

        candidate = detect_cross_indication(signal)

        if candidate:
            cross_indication_signals.append(candidate)

            print("\n" + "=" * 60)
            print("🚨 CROSS-INDICATION SIGNAL")
            print("=" * 60)

            print(
                "Drug:",
                candidate["drug"]
            )

            print(
                "Existing indication:",
                ", ".join(
                    candidate["existing_indications"]
                )
            )

            print(
                "New indication:",
                candidate["new_indication"]
            )

            print(
                "Target:",
                candidate["target"]
            )

            print(
                "Evidence score:",
                candidate["evidence_score"]
            )"""

    print("\n[5] Building evidence graph...")

    graph = EvidenceGraph(
        known_indications=KNOWN_INDICATIONS
    )

    for relation in all_relationships:

        evidence = relation["evidence"]

        if relation["type"] == "drug_target":

            graph.add_drug_target(
                relation["drug"],
                relation["target"],
                evidence
            )

        elif relation["type"] == "target_disease":

            graph.add_target_disease(
                relation["target"],
                relation["disease"],
                evidence
            )

    print("Evidence graph constructed.")

    print("\n[6] Inferring new indications...")

    inferred = graph.infer_new_indications()

    print(
        f"Found {len(inferred)} inferred candidates."
    )

    for candidate in inferred:

        print("\n" + "=" * 60)

        print("🚨 POTENTIAL REPURPOSING SIGNAL")

        print(
            "Drug:",
            candidate["drug"]
        )

        print(
            "Target:",
            candidate["target"]
        )

        print(
            "Potential disease:",
            candidate["disease"]
        )

        print(
            "Reason:",
            candidate["reason"]
        )


    print("\n[7] Searching independent target-disease evidence...")

    ids = search_pubmed(
        "S1P receptor",
        "Alzheimer's disease"
    )

    print(
        "PubMed records found:",
        len(ids)
    )

    print(
        "PMIDs:",
        ids
    )

if __name__ == "__main__":
    main()