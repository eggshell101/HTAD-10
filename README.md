# HTAD-10

## Hypothesis-to-Action Discovery Engine

HTAD-10 is an AI-assisted biomedical discovery platform designed to identify and prioritize potential drug–disease relationships from heterogeneous biomedical evidence.

The system combines live biomedical literature and clinical-trial retrieval, AI-based relationship extraction, evidence-graph reasoning, classical evidence scoring, and quantum optimization using Qiskit QAOA.

---

## Overview

Drug repurposing requires connecting evidence distributed across scientific literature, clinical trials, molecular targets, and disease mechanisms.

HTAD-10 attempts to automate this process through an end-to-end pipeline:

```text
User Query
    │
    ▼
Entity Resolution
    │
    ▼
Live Biomedical Search
    │
    ├── PubMed
    ├── medRxiv
    └── ClinicalTrials.gov
    │
    ▼
AI Relationship Extraction
    │
    ▼
Evidence Graph
    │
    ▼
Candidate Inference
    │
    ├───────────────────┐
    ▼                   ▼
Classical Evidence     QUBO
Scoring                  │
    │                    ▼
    │                Qiskit QAOA
    │                    │
    └──────────┬─────────┘
               ▼
          HTAD-10 Score
               │
               ▼
              GUI
