"""
BB84 QKD — Iteration 1: Ideal Baseline + Intercept–Resend Attack
=================================================================
Research-grade circuit-level evaluation of the BB84 protocol using
Qiskit AerSimulator.

Execution modes
---------------
1. Ideal baseline  — AerSimulator, no noise, no adversary  → QBER ≈ 0%
2. Intercept–resend — Eve-equivalent Pauli channel on 'id' markers → QBER ≈ 25%

Scientific framing
------------------
This is a circuit-level experimental cryptographic evaluation under
controlled simulation. It does NOT claim production-ready QKD or
absolute security guarantees.

Usage
-----
    python bb84_iteration1.py

Requirements
------------
    qiskit >= 1.0
    qiskit-aer >= 0.14
    numpy >= 1.24
    matplotlib >= 3.7
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, pauli_error


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
BitArray   = List[int]
BasisArray = List[int]   # 0 = Z-basis, 1 = X-basis
Counts     = Dict[str, int]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ExperimentConfig:
    """
    Immutable configuration for a single BB84 experiment run.

    Attributes
    ----------
    n_qubits     : Number of qubits (protocol length).
    shots        : Number of circuit shots for statistical averaging.
    sample_size  : Number of sifted bits revealed for QBER estimation.
    seed         : Master RNG seed for bits/bases generation.
    seed_sim     : Seed forwarded to AerSimulator for reproducibility.
    seed_transpiler : Seed forwarded to Qiskit transpiler.
    """

    n_qubits:        int           = 256
    shots:           int           = 4096
    sample_size:     int           = 64
    seed:            int           = 42
    seed_sim:        Optional[int] = 42
    seed_transpiler: Optional[int] = 42


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------
def generate_bits_and_bases(
    n: int,
    seed: Optional[int],
) -> Tuple[BitArray, BasisArray]:
    """
    Generate a random bit string and basis string of length n.

    Parameters
    ----------
    n    : Length of the arrays.
    seed : RNG seed. Pass None for non-reproducible runs.

    Returns
    -------
    bits  : List of 0/1 integers.
    bases : List of 0 (Z-basis) / 1 (X-basis) integers.
    """
    rng   = np.random.default_rng(seed)
    bits  = rng.integers(0, 2, size=n, dtype=int).tolist()
    bases = rng.integers(0, 2, size=n, dtype=int).tolist()
    return bits, bases


# ---------------------------------------------------------------------------
# Circuit construction
# ---------------------------------------------------------------------------
def build_bb84_circuit(
    alice_bits:  Sequence[int],
    alice_bases: Sequence[int],
    bob_bases:   Sequence[int],
    *,
    insert_eve_markers: bool = False,
) -> QuantumCircuit:
    """
    Construct the BB84 prepare-and-measure circuit.

    Alice prepares each qubit in the chosen bit/basis combination.
    Bob applies his basis rotation and measures.

    Parameters
    ----------
    alice_bits        : Alice's random bits (0 or 1).
    alice_bases       : Alice's encoding bases (0=Z, 1=X).
    bob_bases         : Bob's measurement bases (0=Z, 1=X).
    insert_eve_markers: If True, inserts 'id' gates between Alice prep and
                        Bob measurement. These gates act as injection points
                        for an Eve-equivalent noise channel.

    Returns
    -------
    QuantumCircuit ready to be transpiled and run.
    """
    n = len(alice_bits)
    if not (n == len(alice_bases) == len(bob_bases)):
        raise ValueError(
            f"Input arrays must have equal length; "
            f"got {n}, {len(alice_bases)}, {len(bob_bases)}."
        )

    qc = QuantumCircuit(n, n, name="bb84")

    # --- Alice: state preparation ---
    for i in range(n):
        if alice_bits[i] == 1:
            qc.x(i)          # flip to |1⟩
        if alice_bases[i] == 1:
            qc.h(i)          # rotate to X-basis (|+⟩ or |−⟩)

    # --- Optional Eve marker gates ---
    if insert_eve_markers:
        qc.barrier()
        for i in range(n):
            qc.id(i)         # identity — noise channel is attached here
        qc.barrier()

    # --- Bob: basis rotation + measurement ---
    for i in range(n):
        if bob_bases[i] == 1:
            qc.h(i)          # rotate X-basis back before measuring
        qc.measure(i, i)

    return qc


# ---------------------------------------------------------------------------
# Noise model — intercept–resend equivalent channel
# ---------------------------------------------------------------------------
def build_intercept_resend_noise_model() -> NoiseModel:
    """
    Build a Pauli noise channel that is statistically equivalent to Eve
    performing an intercept–resend attack with random basis selection.

    Derivation
    ----------
    Eve picks a random basis (Z or X) with equal probability.
    When Eve's basis matches Alice's, no error is introduced.
    When it does not match (prob = 0.5), the state is randomly
    flipped with equal probability in the wrong basis, which
    maps to the Pauli channel:

        ρ → 0.50·I·ρ·I + 0.25·X·ρ·X + 0.25·Z·ρ·Z

    This channel is attached to 'id' marker gates so it fires
    exactly once per qubit between Alice's preparation and Bob's
    measurement, matching the intercept–resend timing.

    Expected QBER: ≈ 25% (established in BB84 foundational literature).
    """
    nm          = NoiseModel()
    eve_channel = pauli_error([("I", 0.50), ("X", 0.25), ("Z", 0.25)])
    nm.add_all_qubit_quantum_error(eve_channel, ["id"])
    return nm


# ---------------------------------------------------------------------------
# Backend execution
# ---------------------------------------------------------------------------
def run_backend(
    circuit:        QuantumCircuit,
    shots:          int,
    seed_sim:       Optional[int],
    seed_transpiler: Optional[int],
    noise_model:    Optional[NoiseModel] = None,
) -> Counts:
    """
    Transpile and run a circuit on AerSimulator.

    Uses the stabilizer method, which is exact and efficient for
    Clifford circuits (BB84 uses only H, X, CNOT, and measurement).

    Parameters
    ----------
    circuit         : The circuit to execute.
    shots           : Number of measurement shots.
    seed_sim        : AerSimulator seed.
    seed_transpiler : Transpiler seed.
    noise_model     : Optional noise model (e.g., Eve-equivalent channel).

    Returns
    -------
    counts : Dictionary mapping bitstrings to observed frequencies.
    """
    clifford_basis = ["id", "x", "z", "h", "s", "sdg", "cx", "reset", "measure"]

    backend = AerSimulator(method="stabilizer", noise_model=noise_model)

    transpiled = transpile(
        circuit,
        basis_gates=clifford_basis,
        optimization_level=1,
        seed_transpiler=seed_transpiler,
    )

    result = backend.run(
        transpiled,
        shots=shots,
        seed_simulator=seed_sim,
    ).result()

    return result.get_counts()


# ---------------------------------------------------------------------------
# Measurement extraction
# ---------------------------------------------------------------------------
def _bitstring_to_bits(bitstring: str, n_bits: int) -> List[int]:
    """
    Convert a Qiskit MSB-first bitstring to a list indexed by classical bit.

    Qiskit returns bitstrings in big-endian order (MSB left), so classical
    bit 0 is the *rightmost* character. Reversing aligns index i with bit i.

    Parameters
    ----------
    bitstring : Raw Qiskit measurement string.
    n_bits    : Expected number of classical bits.

    Returns
    -------
    List[int] where element i is the value of classical bit i.
    """
    if len(bitstring) != n_bits:
        raise ValueError(
            f"Bitstring length {len(bitstring)} does not match "
            f"expected {n_bits} bits."
        )
    return [int(ch) for ch in reversed(bitstring)]


# ---------------------------------------------------------------------------
# Key sifting
# ---------------------------------------------------------------------------
def sift_keys(
    alice_bases: Sequence[int],
    bob_bases:   Sequence[int],
) -> List[int]:
    """
    Return indices where Alice and Bob used the same measurement basis.

    Parameters
    ----------
    alice_bases : Alice's encoding bases.
    bob_bases   : Bob's measurement bases.

    Returns
    -------
    List of matching indices (the sifted key positions).
    """
    if len(alice_bases) != len(bob_bases):
        raise ValueError("alice_bases and bob_bases must have equal length.")
    return [i for i, (a, b) in enumerate(zip(alice_bases, bob_bases)) if a == b]


def _sample_positions(
    sifted: Sequence[int],
    k:      int,
    seed:   Optional[int],
) -> List[int]:
    """
    Randomly select k positions from the sifted key for QBER estimation.

    These positions are sacrificed (publicly revealed) to estimate error rate.

    Parameters
    ----------
    sifted : Full list of sifted key indices.
    k      : Number of positions to sample.
    seed   : RNG seed.

    Returns
    -------
    List of sampled positions.
    """
    if not sifted:
        return []
    rng = np.random.default_rng(seed)
    k   = min(k, len(sifted))
    return rng.choice(list(sifted), size=k, replace=False).tolist()


# ---------------------------------------------------------------------------
# QBER estimation
# ---------------------------------------------------------------------------
def estimate_qber(
    counts:           Counts,
    alice_bits:       Sequence[int],
    sample_positions: Sequence[int],
    n_qubits:         int,
) -> Tuple[int, float]:
    """
    Estimate the Quantum Bit Error Rate (QBER) from measurement counts.

    QBER is defined as:
        QBER = (number of mismatched bits) / (total bit comparisons)

    Comparisons are weighted by shot count so all shots contribute equally.

    Parameters
    ----------
    counts           : Shot counts returned by AerSimulator.
    alice_bits       : Alice's original bit values (ground truth).
    sample_positions : Indices of sifted bits selected for QBER check.
    n_qubits         : Total number of qubits in the circuit.

    Returns
    -------
    (errors_in_sample, QBER)
    """
    if not sample_positions:
        return 0, 0.0

    total_shots     = sum(counts.values())
    total_comparisons = total_shots * len(sample_positions)
    mismatches      = 0

    for bitstring, count in counts.items():
        bob_bits = _bitstring_to_bits(bitstring, n_qubits)
        for pos in sample_positions:
            if bob_bits[pos] != int(alice_bits[pos]):
                mismatches += count

    qber = mismatches / total_comparisons if total_comparisons > 0 else 0.0
    return int(mismatches), float(qber)


# ---------------------------------------------------------------------------
# Metrics reporting
# ---------------------------------------------------------------------------
def summarize_metrics(
    *,
    mode:             str,
    cfg:              ExperimentConfig,
    backend_name:     str,
    disturbance_type: str,
    sifted_positions: Sequence[int],
    sample_size:      int,
    errors_in_sample: int,
    qber:             float,
) -> Dict[str, Any]:
    """
    Assemble a structured metrics dictionary for a single experiment run.

    Returns
    -------
    Dict matching the project's canonical metrics schema.
    """
    raw_key_length    = cfg.n_qubits
    sifted_key_length = len(sifted_positions)
    retention_rate    = sifted_key_length / raw_key_length if raw_key_length else 0.0

    return {
        "mode":               mode,
        "n_qubits":           int(raw_key_length),
        "shots":              int(cfg.shots),
        "seed":               int(cfg.seed),
        "backend_name":       backend_name,
        "disturbance_type":   disturbance_type,
        "raw_key_length":     int(raw_key_length),
        "sifted_key_length":  int(sifted_key_length),
        "retention_rate":     round(float(retention_rate), 4),
        "sample_size":        int(sample_size),
        "errors_in_sample":   int(errors_in_sample),
        "QBER":               round(float(qber), 4),
    }


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------
def run_ideal_bb84(cfg: ExperimentConfig) -> Dict[str, Any]:
    """
    Run BB84 on AerSimulator with no noise and no adversary.

    Expected QBER ≈ 0%  (correctness baseline).
    """
    alice_bits,  alice_bases = generate_bits_and_bases(cfg.n_qubits, cfg.seed)
    _,           bob_bases   = generate_bits_and_bases(cfg.n_qubits, cfg.seed + 1)

    qc = build_bb84_circuit(
        alice_bits, alice_bases, bob_bases,
        insert_eve_markers=False,
    )
    counts = run_backend(
        qc,
        shots=cfg.shots,
        seed_sim=cfg.seed_sim,
        seed_transpiler=cfg.seed_transpiler,
        noise_model=None,
    )

    sifted     = sift_keys(alice_bases, bob_bases)
    sample_pos = _sample_positions(sifted, cfg.sample_size, cfg.seed)
    errors, qber = estimate_qber(counts, alice_bits, sample_pos, cfg.n_qubits)

    return summarize_metrics(
        mode="ideal",
        cfg=cfg,
        backend_name="AerSimulator(stabilizer)",
        disturbance_type="none",
        sifted_positions=sifted,
        sample_size=len(sample_pos),
        errors_in_sample=errors,
        qber=qber,
    )


def run_intercept_resend(cfg: ExperimentConfig) -> Dict[str, Any]:
    """
    Run BB84 with an Eve-equivalent intercept–resend Pauli channel.

    Eve measures each qubit in a random basis and re-sends the post-
    measurement state. This is implemented as a Pauli channel on 'id'
    marker gates inserted between Alice's preparation and Bob's measurement.

    Expected QBER ≈ 25%  (as established in BB84/QKD literature).
    """
    alice_bits,  alice_bases = generate_bits_and_bases(cfg.n_qubits, cfg.seed)
    _,           bob_bases   = generate_bits_and_bases(cfg.n_qubits, cfg.seed + 1)

    qc = build_bb84_circuit(
        alice_bits, alice_bases, bob_bases,
        insert_eve_markers=True,
    )
    noise_model = build_intercept_resend_noise_model()

    counts = run_backend(
        qc,
        shots=cfg.shots,
        seed_sim=cfg.seed_sim,
        seed_transpiler=cfg.seed_transpiler,
        noise_model=noise_model,
    )

    sifted     = sift_keys(alice_bases, bob_bases)
    sample_pos = _sample_positions(sifted, cfg.sample_size, cfg.seed)
    errors, qber = estimate_qber(counts, alice_bits, sample_pos, cfg.n_qubits)

    return summarize_metrics(
        mode="intercept_resend",
        cfg=cfg,
        backend_name="AerSimulator(stabilizer)+PauliChannel",
        disturbance_type="intercept_resend_equivalent_channel",
        sifted_positions=sifted,
        sample_size=len(sample_pos),
        errors_in_sample=errors,
        qber=qber,
    )


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------
def run_sanity_checks() -> None:
    """
    Run mandatory correctness checks before the main experiment.

    Checks
    ------
    1. Ideal QBER is effectively zero (< 2%).
    2. Intercept–resend QBER is significantly elevated (> 10%).
    3. Sifting retention rate is approximately 50% (± 15%).

    Raises
    ------
    AssertionError if any check fails, with a descriptive message.
    """
    test_cfg = ExperimentConfig(
        n_qubits=64, shots=2048, sample_size=32,
        seed=7, seed_sim=7, seed_transpiler=7,
    )

    print("Running sanity checks ...")
    ideal = run_ideal_bb84(test_cfg)
    ir    = run_intercept_resend(test_cfg)

    assert ideal["QBER"] < 0.02, (
        f"FAIL — Ideal QBER too high: {ideal['QBER']:.4f} "
        f"(expected < 0.02). Full metrics: {ideal}"
    )
    assert ir["QBER"] > 0.10, (
        f"FAIL — Intercept–resend QBER too low: {ir['QBER']:.4f} "
        f"(expected > 0.10). Full metrics: {ir}"
    )
    assert abs(ideal["retention_rate"] - 0.5) < 0.15, (
        f"FAIL — Sifting retention rate out of expected range: "
        f"{ideal['retention_rate']:.4f} (expected 0.35–0.65). Full metrics: {ideal}"
    )

    print("  [PASS] Ideal QBER < 2%")
    print(f"         Ideal QBER = {ideal['QBER']:.4f}")
    print("  [PASS] Intercept–resend QBER > 10%")
    print(f"         IR QBER    = {ir['QBER']:.4f}")
    print(f"  [PASS] Sifting retention ≈ 50%")
    print(f"         Retention  = {ideal['retention_rate']:.4f}")
    print("Sanity checks passed.\n")


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def plot_qber_comparison(
    metrics_ideal: Dict[str, Any],
    metrics_ir:    Dict[str, Any],
) -> None:
    """
    Plot a side-by-side QBER bar chart comparing the two experimental modes.

    Parameters
    ----------
    metrics_ideal : Metrics dict from run_ideal_bb84().
    metrics_ir    : Metrics dict from run_intercept_resend().
    """
    labels = ["Ideal\n(no adversary)", "Intercept–Resend\n(Eve-equivalent)"]
    qbers  = [metrics_ideal["QBER"], metrics_ir["QBER"]]
    colors = ["steelblue", "tomato"]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, qbers, color=colors, width=0.4, edgecolor="black", linewidth=0.8)

    # Annotate each bar with its numeric value
    for bar, q in zip(bars, qbers):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.005,
            f"{q:.4f}",
            ha="center", va="bottom", fontsize=11,
        )

    # Reference line: theoretical BB84 intercept–resend threshold
    ax.axhline(0.25, color="firebrick", linestyle="--", linewidth=1.2, label="Theoretical IR QBER = 0.25")
    ax.axhline(0.11, color="orange",    linestyle=":",  linewidth=1.2, label="Security threshold ≈ 0.11")

    ax.set_ylim(0, 0.35)
    ax.set_ylabel("QBER (Quantum Bit Error Rate)", fontsize=12)
    ax.set_title("BB84 Iteration 1 — QBER: Ideal vs Intercept–Resend Attack", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.4)

    plt.tight_layout()
    plt.savefig("qber_comparison.png", dpi=150)
    plt.show()
    print("Plot saved → qber_comparison.png")


def plot_sifting_retention(metrics: Dict[str, Any]) -> None:
    """
    Plot a bar chart showing the number of retained vs discarded bits after sifting.

    Parameters
    ----------
    metrics : Metrics dict from any experiment run.
    """
    retained  = metrics["sifted_key_length"]
    discarded = metrics["raw_key_length"] - retained

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["Retained", "Discarded"], [retained, discarded], color=["steelblue", "tomato"],
           edgecolor="black", linewidth=0.8)

    ax.set_ylabel("Number of Bits", fontsize=12)
    ax.set_title(f"Sifting Retention — {metrics['mode']} mode", fontsize=12)
    ax.grid(axis="y", alpha=0.4)

    plt.tight_layout()
    plt.savefig("sifting_retention.png", dpi=150)
    plt.show()
    print("Plot saved → sifting_retention.png")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Main experiment runner for BB84 Iteration 1.

    Execution order
    ---------------
    1. Run sanity checks.
    2. Run ideal BB84 simulation.
    3. Run intercept–resend simulation.
    4. Print structured metrics (JSON).
    5. Produce comparison plots.
    """
    print("=" * 60)
    print("BB84 QKD — Iteration 1: Ideal + Intercept–Resend")
    print("=" * 60)
    print()

    # Step 1: Sanity checks
    run_sanity_checks()

    # Step 2: Main experiment config
    cfg = ExperimentConfig(
        n_qubits=256, shots=4096, sample_size=64,
        seed=42, seed_sim=42, seed_transpiler=42,
    )

    # Step 3: Run experiments
    print("Running ideal BB84 simulation ...")
    metrics_ideal = run_ideal_bb84(cfg)
    print("  Done.\n")

    print("Running intercept–resend simulation ...")
    metrics_ir = run_intercept_resend(cfg)
    print("  Done.\n")

    # Step 4: Print structured metrics
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    all_results = {
        "iteration":     1,
        "description":   "Ideal baseline + Intercept-Resend attack simulation",
        "ideal":         metrics_ideal,
        "intercept_resend": metrics_ir,
    }

    print(json.dumps(all_results, indent=2))
    print()

    # Step 5: Distinguishability check
    print("=" * 60)
    print("DISTINGUISHABILITY ANALYSIS")
    print("=" * 60)
    delta = metrics_ir["QBER"] - metrics_ideal["QBER"]
    print(f"  Ideal QBER          : {metrics_ideal['QBER']:.4f}")
    print(f"  Intercept–Resend QBER: {metrics_ir['QBER']:.4f}")
    print(f"  ΔQBER (IR - Ideal)  : {delta:.4f}")
    print()

    if delta > 0.10:
        print("  [CONCLUSION] Adversarial QBER is statistically distinguishable")
        print("               from ideal hardware noise. BB84 would detect Eve.")
    else:
        print("  [WARNING] ΔQBER below expected threshold. Review configuration.")
    print()

    # Step 6: Plots
    print("Generating plots ...")
    plot_qber_comparison(metrics_ideal, metrics_ir)
    plot_sifting_retention(metrics_ideal)

    print()
    print("Iteration 1 complete.")


if __name__ == "__main__":
    main()
