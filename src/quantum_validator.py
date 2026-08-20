"""
HTAD-10 Quantum Validator
=========================

Real Qiskit QAOA implementation for the HTAD-10 evidence-consistency QUBO.

Pipeline:

    Candidate
        |
        v
    Evidence features
        |
        v
    3-variable QUBO
        |
        +----------------------+
        |                      |
        v                      v
    Exact classical        Qiskit QAOA
    reference              quantum circuit
        |                      |
        +----------+-----------+
                   |
                   v
          Energy / state comparison
                   |
                   v
          Quantum validation result

Important:
- QAOA is actually executed with Qiskit.
- AerSimulator is used by default, so this runs locally.
- The exact classical solution is retained as the ground-truth
  reference for this tiny 3-qubit problem.
- This does NOT claim quantum advantage.
- It does provide an actual QAOA execution and comparison.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Tuple


# ============================================================
# QISKIT
# ============================================================

try:

    from qiskit import (
        QuantumCircuit,
    )

    from qiskit_aer import (
        AerSimulator,
    )

    from qiskit_optimization import (
        QuadraticProgram,
    )

    from qiskit_optimization.algorithms import (
        MinimumEigenOptimizer,
    )

    from qiskit_optimization.minimum_eigensolvers import (
        QAOA,
    )

    from qiskit_optimization.optimizers import (
        COBYLA,
    )

    QISKIT_AVAILABLE = True

except Exception as exc:

    QISKIT_AVAILABLE = False

    QISKIT_IMPORT_ERROR = str(
        exc
    )


# ============================================================
# UTILITIES
# ============================================================

def _clip(
    value: float,
    low: float = 0.0,
    high: float = 1.0,
) -> float:

    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return low

    return max(
        low,
        min(
            high,
            value,
        ),
    )


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def build_features(
    candidate: Dict[str, Any],
) -> Dict[str, float]:
    """
    Convert HTAD evidence into normalized quantum features.
    """

    ai_confidence = candidate.get(
        "ai_confidence",
        candidate.get(
            "drug_target_confidence",
            0.0,
        ),
    )

    target_disease_confidence = candidate.get(
        "target_disease_confidence",
        0.0,
    )

    classical_score = candidate.get(
        "classical_score",
        candidate.get(
            "evidence_score",
            candidate.get(
                "score",
                0.0,
            ),
        ),
    )

    return {

        "ai_confidence":
            _clip(
                ai_confidence
            ),

        "target_disease_confidence":
            _clip(
                target_disease_confidence
            ),

        "classical_score":
            _clip(
                float(
                    classical_score
                )
                / 100.0
            ),
    }


# ============================================================
# QUBO
# ============================================================

def build_qubo(
    features: Dict[str, float],
) -> Dict[Tuple[int, int], float]:
    """
    Build the HTAD-10 evidence-consistency QUBO.

    Variables:

        x0 = drug-target evidence selected
        x1 = target-disease evidence selected
        x2 = candidate selected

    Minimize:

        E(x)
          = Σ Qij xi xj
    """

    ai = _clip(
        features.get(
            "ai_confidence",
            0.0,
        )
    )

    td = _clip(
        features.get(
            "target_disease_confidence",
            0.0,
        )
    )

    classical = _clip(
        features.get(
            "classical_score",
            0.0,
        )
    )

    return {

        # Individual evidence
        (0, 0): -ai,
        (1, 1): -td,
        (2, 2): -classical,

        # Drug-target / target-disease consistency
        (0, 1):
            -0.5 * min(
                ai,
                td,
            ),

        # Drug-target / candidate consistency
        (0, 2):
            -0.5 * ai,

        # Target-disease / candidate consistency
        (1, 2):
            -0.5 * td,
    }


# ============================================================
# QUBO EVALUATION
# ============================================================

def evaluate_bitstring(
    bitstring: str,
    Q: Dict[Tuple[int, int], float],
) -> float:

    if len(
        bitstring
    ) != 3:

        raise ValueError(
            "HTAD-10 QUBO requires 3 bits."
        )

    bits = [
        int(x)
        for x in bitstring
    ]

    energy = 0.0

    for (
        i,
        j,
    ), coefficient in Q.items():

        energy += (
            coefficient
            * bits[i]
            * bits[j]
        )

    return float(
        energy
    )


# ============================================================
# EXACT CLASSICAL REFERENCE
# ============================================================

def classical_optimize(
    Q: Dict[Tuple[int, int], float],
) -> Dict[str, Any]:
    """
    Exact classical solution.

    Because the QUBO contains only three variables,
    all 8 states are enumerated.
    """

    best_state = None

    best_energy = float(
        "inf"
    )

    states = []

    for number in range(8):

        bitstring = format(
            number,
            "03b",
        )

        energy = evaluate_bitstring(
            bitstring,
            Q,
        )

        states.append(
            {
                "state": bitstring,
                "energy": energy,
            }
        )

        if energy < best_energy:

            best_energy = energy
            best_state = bitstring

    return {

        "state":
            best_state,

        "energy":
            best_energy,

        "states":
            states,

        "method":
            "exact_classical",
    }


# ============================================================
# QISKIT QUADRATIC PROGRAM
# ============================================================

def build_quadratic_program(
    Q: Dict[Tuple[int, int], float],
) -> "QuadraticProgram":
    """
    Convert our internal QUBO dictionary into a Qiskit
    QuadraticProgram.

    Qiskit then converts the binary quadratic program into
    the corresponding Ising Hamiltonian for QAOA.
    """

    if not QISKIT_AVAILABLE:

        raise RuntimeError(
            "Qiskit is not available. "
            "Install qiskit, qiskit-aer and "
            "qiskit-optimization."
        )

    problem = QuadraticProgram(
        name="HTAD10_Evidence_QUBO"
    )

    problem.binary_var(
        name="x0"
    )

    problem.binary_var(
        name="x1"
    )

    problem.binary_var(
        name="x2"
    )

    linear = {}

    quadratic = {}

    for (
        i,
        j,
    ), coefficient in Q.items():

        if i == j:

            linear[
                f"x{i}"
            ] = float(
                coefficient
            )

        else:

            quadratic[
                (
                    f"x{i}",
                    f"x{j}",
                )
            ] = float(
                coefficient
            )

    problem.minimize(
        linear=linear,
        quadratic=quadratic,
    )

    return problem


# ============================================================
# BITSTRING EXTRACTION
# ============================================================

def _extract_qaoa_bitstring(
    result: Any,
) -> str:
    """
    Extract a three-bit solution from Qiskit Optimization.
    """

    x = getattr(
        result,
        "x",
        None,
    )

    if x is None:

        raise RuntimeError(
            "QAOA did not return a solution vector."
        )

    bits = []

    for value in x:

        bits.append(
            "1"
            if float(value) >= 0.5
            else "0"
        )

    return "".join(
        bits
    )


# ============================================================
# QAOA EXECUTION
# ============================================================

def run_qaoa(
    Q: Dict[Tuple[int, int], float],
    reps: int = 2,
    shots: int = 2048,
) -> Dict[str, Any]:
    """
    Execute real QAOA using Qiskit.

    Backend:
        Local AerSimulator.

    The optimization of the QAOA angles is classical, while
    the objective evaluations are obtained from quantum circuits.
    """

    if not QISKIT_AVAILABLE:

        return {

            "success":
                False,

            "error":
                QISKIT_IMPORT_ERROR,

            "method":
                "qaoa",

        }

    problem = build_quadratic_program(
        Q
    )

    backend = AerSimulator()

    # --------------------------------------------------------
    # Qiskit 0.7-compatible QAOA setup
    # --------------------------------------------------------

    try:

        from qiskit_aer.primitives import (
            SamplerV2,
        )

        sampler = SamplerV2(
            seed=42,
            default_shots=shots,
        )

        optimizer = COBYLA(
            maxiter=100
        )

        qaoa = QAOA(
            sampler=sampler,
            optimizer=optimizer,
            reps=reps,
        )

        optimizer_wrapper = (
            MinimumEigenOptimizer(
                qaoa
            )
        )

        result = optimizer_wrapper.solve(
            problem
        )

        state = _extract_qaoa_bitstring(
            result
        )

        energy = evaluate_bitstring(
            state,
            Q,
        )

        return {

            "success":
                True,

            "state":
                state,

            "energy":
                float(
                    energy
                ),

            "objective":
                float(
                    result.fval
                ),

            "reps":
                reps,

            "shots":
                shots,

            "backend":
                "AerSimulator",

            "method":
                "Qiskit QAOA",

        }

    except Exception as exc:

        return {

            "success":
                False,

            "error":
                str(exc),

            "backend":
                "AerSimulator",

            "method":
                "Qiskit QAOA",

        }


# ============================================================
# VALIDATION SCORE
# ============================================================

def validation_score_from_energy(
    energy: float,
) -> float:
    """
    Convert QUBO energy to a 0-100 consistency score.

    This score represents evidence consistency.

    It is NOT:
        - a probability,
        - clinical efficacy,
        - quantum advantage.
    """

    normalized = (
        1.0
        - math.exp(
            float(
                energy
            )
        )
    )

    normalized = _clip(
        normalized
    )

    return round(
        normalized * 100.0,
        2,
    )


# Backwards compatibility
quantum_score_from_energy = (
    validation_score_from_energy
)


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate_candidate(
    candidate: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Complete HTAD-10 quantum validation.

    Runs BOTH:

        1. Exact classical QUBO optimization.
        2. Real Qiskit QAOA.

    The classical result is used as the exact reference.

    The QAOA result is used as the quantum result.
    """

    # --------------------------------------------------------
    # Features
    # --------------------------------------------------------

    features = build_features(
        candidate
    )

    # --------------------------------------------------------
    # QUBO
    # --------------------------------------------------------

    Q = build_qubo(
        features
    )

    # --------------------------------------------------------
    # Exact classical reference
    # --------------------------------------------------------

    classical = classical_optimize(
        Q
    )

    classical_energy = (
        classical["energy"]
    )

    classical_state = (
        classical["state"]
    )

    # --------------------------------------------------------
    # Actual QAOA
    # --------------------------------------------------------

    qaoa = run_qaoa(
        Q,
        reps=2,
        shots=2048,
    )

    # --------------------------------------------------------
    # QAOA successful
    # --------------------------------------------------------

    if qaoa.get(
        "success",
        False,
    ):

        qaoa_energy = float(
            qaoa["energy"]
        )

        qaoa_state = qaoa[
            "state"
        ]

        qaoa_score = (
            validation_score_from_energy(
                qaoa_energy
            )
        )

        # Exact agreement
        exact_match = (
            abs(
                qaoa_energy
                - classical_energy
            )
            < 1e-9
        )

        # Approximation ratio for minimization.
        #
        # Since both energies are negative, use magnitudes
        # relative to zero. Exact optimum => 1.0.
        if classical_energy < 0:

            approximation_ratio = _clip(
                abs(qaoa_energy)
                / abs(classical_energy)
            )

        else:

            approximation_ratio = 1.0

        status = (
            "validated"
            if exact_match
            else "qaoa_executed"
        )

        return {

            "quantum_score":
                qaoa_score,

            "quantum_energy":
                round(
                    qaoa_energy,
                    6,
                ),

            "quantum_state":
                qaoa_state,

            "quantum_features":
                features,

            "quantum_method":
                "Qiskit QAOA",

            "quantum_status":
                status,

            "quantum_backend":
                qaoa.get(
                    "backend"
                ),

            "quantum_executed":
                True,

            "quantum_advantage":
                False,

            "qaoa_reps":
                qaoa.get(
                    "reps"
                ),

            "qaoa_shots":
                qaoa.get(
                    "shots"
                ),

            "classical_energy":
                round(
                    classical_energy,
                    6,
                ),

            "classical_state":
                classical_state,

            "energy_gap":
                round(
                    qaoa_energy
                    - classical_energy,
                    6,
                ),

            "approximation_ratio":
                round(
                    approximation_ratio,
                    6,
                ),

            "exact_match":
                exact_match,

            "qubo":
                Q,

        }

    # --------------------------------------------------------
    # QAOA failed
    # --------------------------------------------------------

    return {

        # Do NOT pretend the classical result is quantum.
        "quantum_score":
            0.0,

        "quantum_energy":
            None,

        "quantum_state":
            None,

        "quantum_features":
            features,

        "quantum_method":
            "Qiskit QAOA",

        "quantum_status":
            "error",

        "quantum_backend":
            "AerSimulator",

        "quantum_executed":
            False,

        "quantum_advantage":
            False,

        "classical_energy":
            round(
                classical_energy,
                6,
            ),

        "classical_state":
            classical_state,

        "energy_gap":
            None,

        "approximation_ratio":
            None,

        "exact_match":
            False,

        "qubo":
            Q,

        "quantum_error":
            qaoa.get(
                "error",
                "Unknown QAOA error",
            ),
    }