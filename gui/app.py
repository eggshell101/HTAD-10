import os
import sys

# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import plotly.graph_objects as go

from src.pipeline import run_htad


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="HTAD-10 Discovery Engine",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    [data-testid="stMetricValue"] {
        font-family: "Courier New", monospace;
        font-size: 1.8rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    .live-badge {
        padding: 6px 12px;
        border-radius: 15px;
        font-weight: 700;
        display: inline-block;
        border: 1px solid rgba(128,128,128,.35);
    }

    .candidate-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,.25);
        margin-bottom: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = None

if "last_query" not in st.session_state:
    st.session_state.last_query = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚙️ HTAD-10")

    st.caption(
        "Live biomedical evidence discovery engine"
    )

    st.divider()

    # -----------------------------
    # Search
    # -----------------------------

    st.markdown("### 🔎 Search")

    search_drug = st.text_input(
        "Drug",
        placeholder="e.g. Siponimod",
    )

    search_disease = st.text_input(
        "Disease",
        placeholder="e.g. Alzheimer's disease",
    )

    # -----------------------------
    # Score filter
    # -----------------------------

    min_score = st.slider(
        "Minimum Confidence Score",
        min_value=0,
        max_value=100,
        value=0,
        step=1,
    )

    # -----------------------------
    # Sources
    # -----------------------------

    st.markdown("### 📚 Live Data Sources")

    use_trials = st.checkbox(
        "ClinicalTrials.gov",
        value=True,
    )

    use_pubmed = st.checkbox(
        "PubMed",
        value=True,
    )

    use_medrxiv = st.checkbox(
        "medRxiv",
        value=True,
    )

    st.divider()

    # -----------------------------
    # Search button
    # -----------------------------

    search_button = st.button(
        "🔎 RUN LIVE SEARCH",
        type="primary",
        use_container_width=True,
    )

    # -----------------------------
    # Clear
    # -----------------------------

    if st.session_state.results is not None:

        if st.button(
            "🗑️ CLEAR RESULTS",
            use_container_width=True,
        ):

            st.session_state.results = None
            st.session_state.last_query = None

            st.rerun()

    st.divider()

    st.caption(
        "Searches selected biomedical sources in real time."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    # 🧬 HTAD-10
    ## Hypothesis-to-Action Discovery Engine

    **LIVE EVIDENCE DISCOVERY**

    Biomedical literature + clinical-trial evidence  
    + mechanistic relationship inference  
    + transparent HTAD scoring
    """
)

st.markdown(
    '<span class="live-badge">● LIVE SEARCH ENGINE</span>',
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# RUN LIVE SEARCH
# ============================================================

if search_button:

    if not search_drug and not search_disease:

        st.warning(
            "Please enter a drug or disease."
        )

    elif not (
        use_trials
        or use_pubmed
        or use_medrxiv
    ):

        st.warning(
            "Please select at least one data source."
        )

    else:

        with st.spinner(
            "Searching live evidence and constructing the evidence graph..."
        ):

            try:

                result = run_htad(
                    search_drug=search_drug,
                    search_disease=search_disease,
                    use_pubmed=use_pubmed,
                    use_medrxiv=use_medrxiv,
                    use_clinicaltrials=use_trials,
                )

                st.session_state.results = result

                st.session_state.last_query = (
                    search_drug,
                    search_disease,
                )

            except Exception as exc:

                st.error(
                    f"Search failed: {exc}"
                )


# ============================================================
# RESULTS
# ============================================================

results = st.session_state.results


# ============================================================
# EMPTY STATE
# ============================================================

if results is None:

    st.info(
        "👈 Enter a drug or disease and click "
        "**RUN LIVE SEARCH**."
    )

    st.markdown(
        """
        ### Example

        **Drug**

        `Siponimod`

        **Disease**

        `Alzheimer's disease`

        ---

        ### HTAD-10 pipeline

        ```text
        Live Search
             ↓
        PubMed / medRxiv / ClinicalTrials.gov
             ↓
        Relationship Extraction
             ↓
        Evidence Graph
             ↓
        Candidate Inference
             ↓
        HTAD-10 Scoring
             ↓
        Quantum Validation
        ```

        The GUI uses live evidence rather than relying on
        a static candidate list.
        """
    )

    st.stop()


# ============================================================
# SOURCE STATISTICS
# ============================================================

stats = results.get(
    "statistics",
    {},
)

all_candidates = results.get(
    "candidates",
    [],
)

relationships = results.get(
    "relationships",
    [],
)

evidence_records = results.get(
    "evidence",
    [],
)


# ============================================================
# TOP STATISTICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "PubMed",
    stats.get("pubmed", 0),
)

c2.metric(
    "medRxiv",
    stats.get("medrxiv", 0),
)

c3.metric(
    "Clinical Trials",
    stats.get("clinicaltrials", 0),
)

c4.metric(
    "Relationships",
    len(relationships),
)

c5.metric(
    "Candidates",
    len(all_candidates),
)


# ============================================================
# API WARNINGS
# ============================================================

errors = results.get(
    "errors",
    [],
)

if errors:

    with st.expander(
        "⚠️ Data-source warnings"
    ):

        for error in errors:

            st.warning(
                error
            )


st.divider()


# ============================================================
# SCORE HELPER
# ============================================================

def get_score(candidate):

    try:

        return float(
            candidate
            .get("scores", {})
            .get("final", 0)
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


# ============================================================
# GUI SERIALIZATION HELPERS
# ============================================================

def serialize_for_gui(value):
    """
    Convert backend/custom Python objects into Streamlit-safe
    primitive values.

    Streamlit/PyArrow cannot directly serialize objects such as:
        Evidence(...)
        defaultdict
        set
        dataclass instances
    """

    if value is None:
        return None

    # Primitive types
    if isinstance(value, (str, int, float, bool)):
        return value

    # Dictionaries
    if isinstance(value, dict):
        return {
            str(key): serialize_for_gui(val)
            for key, val in value.items()
        }

    # Lists / tuples
    if isinstance(value, (list, tuple)):
        return [
            serialize_for_gui(item)
            for item in value
        ]

    # Sets
    if isinstance(value, set):
        return ", ".join(
            str(serialize_for_gui(item))
            for item in sorted(value, key=str)
        )

    # Dataclass / custom objects
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: serialize_for_gui(
                getattr(value, field_name)
            )
            for field_name in value.__dataclass_fields__
        }

    # Generic objects
    if hasattr(value, "__dict__"):
        return {
            str(key): serialize_for_gui(val)
            for key, val in vars(value).items()
        }

    # Final fallback
    return str(value)


def relationship_to_gui(relationship):
    """
    Convert one backend relationship into a completely
    Streamlit/PyArrow-safe dictionary.
    """

    result = serialize_for_gui(relationship)

    if not isinstance(result, dict):
        return {
            "relationship": str(result)
        }

    # Make evidence readable instead of dumping nested objects
    evidence = result.get("evidence")

    if isinstance(evidence, dict):
        result["evidence_title"] = evidence.get(
            "title",
            ""
        )

        result["evidence_source"] = evidence.get(
            "source",
            ""
        )

        result["evidence_date"] = evidence.get(
            "date",
            ""
        )

        result["evidence_url"] = evidence.get(
            "url",
            ""
        )

        result["evidence_abstract"] = evidence.get(
            "abstract",
            ""
        )

        # Remove complex object from dataframe
        result.pop("evidence", None)

    elif evidence is not None:
        result["evidence"] = str(evidence)

    return result


# ============================================================
# FILTER
# ============================================================

candidates = [
    candidate
    for candidate in all_candidates
    if get_score(candidate) >= min_score
]


candidates.sort(
    key=get_score,
    reverse=True,
)


# ============================================================
# NO CANDIDATES
# ============================================================

if not candidates:

    st.warning(
        "No candidates satisfy the current confidence threshold."
    )

    if all_candidates:

        st.info(
            f"{len(all_candidates)} candidate(s) were discovered, "
            f"but none reached the selected threshold of "
            f"{min_score}."
        )

    st.markdown(
        "### 📚 Retrieved Evidence"
    )

    for item in evidence_records[:20]:

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{item.get('title', 'Untitled')}**"
            )

            st.caption(
                f"{item.get('source', 'Unknown')} | "
                f"{item.get('identifier') or 'No ID'} | "
                f"{item.get('date') or 'Date unavailable'}"
            )

            if item.get("abstract"):

                st.write(
                    item["abstract"][:700]
                )

            if item.get("url"):

                st.link_button(
                    "Open source",
                    item["url"],
                )

    st.stop()


# ============================================================
# CANDIDATE SELECTOR
# ============================================================

labels = []

for candidate in candidates:

    labels.append(
        f"{candidate.get('drug', 'Unknown')} "
        f"→ "
        f"{candidate.get('candidate_disease', 'Unknown')} "
        f"({get_score(candidate):.1f}/100)"
    )


selected_index = st.selectbox(
    "📌 Select Candidate",
    range(len(candidates)),
    format_func=lambda i: labels[i],
)


data = candidates[selected_index]


# ============================================================
# BASIC DATA
# ============================================================

drug = data.get(
    "drug",
    "Unknown",
)

target = data.get(
    "target",
    "Unknown",
)

disease = data.get(
    "candidate_disease",
    "Unknown",
)

scores = data.get(
    "scores",
    {},
)

final_score = get_score(
    data
)


# ============================================================
# PRIORITY CANDIDATE
# ============================================================

st.markdown(
    "## 🚨 Priority Candidate"
)

p1, p2, p3 = st.columns(3)

p1.metric(
    "Drug",
    str(drug).upper(),
)

p2.metric(
    "Potential Indication",
    disease,
)

p3.metric(
    "HTAD-10 Score",
    f"{final_score:.1f}/100",
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🏠 Discovery Dashboard",
        "🧬 Evidence Graph",
        "🔬 Quantum Validation",
        "📚 Literature Audit",
    ]
)


# ============================================================
# TAB 1
# ============================================================

with tab1:

    left, right = st.columns(
        [1.2, 1]
    )


    # --------------------------------------------------------
    # CANDIDATE INFORMATION
    # --------------------------------------------------------

    with left:

        with st.container(
            border=True
        ):

            st.markdown(
                "### 🚨 Potential Repurposing Candidate"
            )

            st.markdown(
                f"# {str(drug).upper()}"
            )

            st.markdown(
                f"**Target:** `{target}`"
            )

            st.markdown(
                f"**Potential indication:** `{disease}`"
            )

            existing = data.get(
                "existing_indications",
                [],
            )

            if existing:

                st.markdown(
                    "**Established indications:** "
                    + ", ".join(existing)
                )

            else:

                st.markdown(
                    "**Established indications:** "
                    "Not available"
                )


        st.markdown("")


        # ----------------------------------------------------
        # EXPLAINABILITY
        # ----------------------------------------------------

        with st.container(
            border=True
        ):

            st.markdown(
                "### 🧠 Explainability"
            )

            st.success(
                "✓ Live evidence retrieved"
            )

            st.success(
                "✓ Relationship extraction performed"
            )

            if (
                target
                and target != "Direct evidence"
                and target != "Unknown"
            ):

                st.success(
                    "✓ Drug → target → disease path detected"
                )

                st.info(
                    f"**Inference path:**\n\n"
                    f"{drug} → {target} → {disease}"
                )

            else:

                st.info(
                    "Direct drug → disease relationship."
                )

            st.write(
                data.get(
                    "reason",
                    "No explanation available.",
                )
            )


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    with right:

        with st.container(
            border=True
        ):

            st.markdown(
                "### HTAD-10 SCORE"
            )

            st.markdown(
                f"""
                <h1 style="
                    text-align:center;
                    font-size:55px;
                    margin-bottom:10px;
                ">
                {final_score:.1f} / 100
                </h1>
                """,
                unsafe_allow_html=True,
            )


            categories = [
                "Clinical",
                "Literature",
                "Mechanistic",
                "Independence",
                "Quantum",
            ]


            values = []

            for category in [
                "clinical",
                "literature",
                "mechanistic",
                "independence",
                "quantum",
            ]:

                try:

                    values.append(
                        float(
                            scores.get(
                                category,
                                0,
                            )
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    values.append(0)


            fig = go.Figure(
                go.Bar(
                    x=values,
                    y=categories,
                    orientation="h",
                    text=[
                        f"{v:.1f}"
                        for v in values
                    ],
                    textposition="auto",
                )
            )


            fig.update_layout(
                height=320,
                margin=dict(
                    l=0,
                    r=0,
                    t=10,
                    b=0,
                ),
                xaxis=dict(
                    range=[0, 100],
                    title="Score",
                ),
                yaxis=dict(
                    title="",
                ),
            )


            st.plotly_chart(
                fig,
                use_container_width=True,
            )


    # --------------------------------------------------------
    # SCORE BREAKDOWN
    # --------------------------------------------------------

    st.markdown(
        "### 📊 Transparent Score Breakdown"
    )


    breakdown = [
        (
            "Clinical",
            scores.get(
                "clinical",
                0,
            ),
        ),
        (
            "Literature",
            scores.get(
                "literature",
                0,
            ),
        ),
        (
            "Mechanistic",
            scores.get(
                "mechanistic",
                0,
            ),
        ),
        (
            "Independence",
            scores.get(
                "independence",
                0,
            ),
        ),
        (
            "Quantum",
            scores.get(
                "quantum",
                0,
            ),
        ),
        (
            "Final HTAD-10",
            scores.get(
                "final",
                0,
            ),
        ),
    ]


    cols = st.columns(
        len(breakdown)
    )


    for col, (
        label,
        value,
    ) in zip(
        cols,
        breakdown,
    ):

        with col:

            try:

                value_text = (
                    f"{float(value):.1f}"
                )

            except (
                TypeError,
                ValueError,
            ):

                value_text = str(value)


            st.metric(
                label,
                value_text,
            )


# ============================================================
# TAB 2 — EVIDENCE GRAPH
# ============================================================

with tab2:

    st.markdown(
        "### 🧬 Mechanistic Evidence Graph"
    )


    if (
        target
        and target != "Unknown"
        and target != "Direct evidence"
    ):

        # --------------------------------------------
        # Visual path
        # --------------------------------------------

        st.markdown(
            f"""
            ## {drug}

            ↓

            ## {target}

            ↓

            ## {disease}
            """
        )


        st.success(
            "Three-node mechanistic path identified."
        )


        # --------------------------------------------
        # Plotly graph
        # --------------------------------------------

        graph = go.Figure()


        # Edges

        graph.add_trace(
            go.Scatter(
                x=[
                    0,
                    0.5,
                    None,
                    0.5,
                    1,
                ],
                y=[
                    0,
                    0.4,
                    None,
                    0.4,
                    0,
                ],
                mode="lines",
                hoverinfo="none",
                line=dict(
                    width=4,
                ),
            )
        )


        # Nodes

        graph.add_trace(
            go.Scatter(
                x=[
                    0,
                    0.5,
                    1,
                ],
                y=[
                    0,
                    0.4,
                    0,
                ],
                mode="markers+text",
                text=[
                    drug,
                    target,
                    disease,
                ],
                textposition="bottom center",
                marker=dict(
                    size=45,
                ),
                hovertemplate=[
                    f"Drug: {drug}<extra></extra>",
                    f"Target: {target}<extra></extra>",
                    f"Disease: {disease}<extra></extra>",
                ],
            )
        )


        graph.update_layout(
            height=450,
            showlegend=False,
            xaxis=dict(
                visible=False,
                range=[
                    -0.2,
                    1.2,
                ],
            ),
            yaxis=dict(
                visible=False,
                range=[
                    -0.35,
                    0.7,
                ],
            ),
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20,
            ),
        )


        st.plotly_chart(
            graph,
            use_container_width=True,
        )


    else:

        st.info(
            f"""
            Direct association:

            **{drug} → {disease}**
            """
        )


    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    st.markdown(
        "### 🔗 Extracted Relationships"
    )

    relevant_relationships = []

    for relationship in relationships:

        if (
            relationship.get("drug") == drug
            or relationship.get("target") == target
            or relationship.get("disease") == disease
        ):
            relevant_relationships.append(
                relationship
            )


    if relevant_relationships:

        # ----------------------------------------------------
        # Convert backend objects → GUI-safe objects
        # ----------------------------------------------------

        gui_relationships = [
            relationship_to_gui(
                relationship
            )
            for relationship in relevant_relationships
        ]

        # ----------------------------------------------------
        # Remove fields that are still complex
        # ----------------------------------------------------

        clean_relationships = []

        for relationship in gui_relationships:

            clean = {}

            for key, value in relationship.items():

                # Guarantee PyArrow-safe values
                if isinstance(
                    value,
                    (str, int, float, bool)
                ) or value is None:

                    clean[key] = value

                else:

                    clean[key] = str(value)

            clean_relationships.append(clean)

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        st.dataframe(
            clean_relationships,
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No additional extracted relationships "
            "for this candidate."
        )


# ============================================================
# TAB 3 — QUANTUM
# ============================================================

with tab3:

    st.markdown(
        "### 🔬 Quantum-Compatible Validation"
    )

    st.info(
        "Quantum validation is kept separate from evidence inference "
        "and reports the prototype's internal plausibility assessment."
    )

    quantum = data.get(
        "quantum_data",
        data.get(
            "quantum",
            data.get(
                "quantum_validation",
                {},
            ),
        ),
    )

    if quantum:

        status = quantum.get(
            "status",
            "unknown",
        )

        method = quantum.get(
            "method",
            "Not specified",
        )

        state = quantum.get(
            "state",
            "Not available",
        )

        try:
            score = float(
                quantum.get(
                    "score",
                    scores.get(
                        "quantum",
                        0.0,
                    ),
                )
                or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            score = 0.0

        q1, q2, q3 = st.columns(3)

        q1.metric(
            "Validation Status",
            str(status),
        )

        q2.metric(
            "Plausibility Score",
            f"{score:.2f}/100",
        )

        q3.metric(
            "Method",
            str(method),
        )

        st.markdown(
            f"**Validation state:** `{state}`"
        )

        features = quantum.get(
            "features",
            {},
        )

        if features:
            st.markdown("#### Quantum Features")
            st.json(features)

        if score >= 75:
            st.success(
                f"The quantum validation prototype assigns a high "
                f"internal plausibility score of {score:.2f}/100 "
                "to this candidate."
            )
        elif score >= 50:
            st.warning(
                f"The quantum validation prototype assigns an "
                f"intermediate plausibility score of {score:.2f}/100."
            )
        else:
            st.error(
                f"The quantum validation prototype assigns a low "
                f"plausibility score of {score:.2f}/100."
            )

        st.caption(
            "Important: this prototype performs QUBO-based "
            "quantum-compatible validation. It does not claim "
            "that a physical quantum processor or molecular VQE "
            "calculation has been executed."
        )


    else:

        st.warning(
            "No quantum validation result is available "
            "for this candidate."
        )

        st.markdown(
            """
            ### Planned validation

            Candidate mechanism
                    ↓
            Molecular fragment / active space
                    ↓
            VQE / quantum chemistry
                    ↓
            Energy difference
                    ↓
            Physics-informed validation
            """
        )


# ============================================================
# TAB 4 — LITERATURE
# ============================================================

with tab4:

    st.markdown(
        "### 📚 Live Literature Audit"
    )


    candidate_evidence = data.get(
        "evidence",
        [],
    )


    # If the candidate itself has no evidence,
    # attempt to use the global evidence records.

    if not candidate_evidence:

        candidate_evidence = evidence_records


    if not candidate_evidence:

        st.info(
            "No supporting evidence records were attached."
        )


    else:

        st.caption(
            f"{len(candidate_evidence)} evidence record(s)"
        )


        for raw_item in candidate_evidence:

            item = serialize_for_gui(raw_item)

            if not isinstance(item, dict):
                item = {
                    "abstract": str(item)
                }

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {item.get('title', 'Untitled evidence')}"
                )


                st.caption(
                    f"{item.get('source', 'Unknown')} | "
                    f"{item.get('identifier') or 'No identifier'} | "
                    f"{item.get('date') or 'Date unavailable'}"
                )


                abstract = item.get(
                    "abstract",
                    "",
                )


                if abstract:

                    with st.expander(
                        "📖 Read evidence summary"
                    ):

                        st.write(
                            abstract
                        )


                if item.get("url"):

                    st.link_button(
                        "🔗 Open source",
                        item["url"],
                    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "HTAD-10 | Live evidence discovery → "
    "mechanistic inference → candidate scoring → "
    "transparent quantum validation"
)