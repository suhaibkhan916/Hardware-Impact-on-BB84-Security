# BB84 QKD — Hardware Impact on Security

Experimental evaluation of the BB84 Quantum Key Distribution protocol on IBM Quantum hardware. The core question is whether natural NISQ device noise can be mistaken for an adversarial intercept-resend attack, and if not, where the detection boundary is.

---

## Research Question

BB84 guarantees that any eavesdropper disturbs the quantum channel in a detectable way. On real superconducting hardware, the device itself introduces errors. This project asks: are those hardware errors small enough that Alice and Bob can still reliably detect an attacker?

---

## Key Results

| Mode | QBER | Notes |
|---|---|---|
| Ideal simulator | 0.00% | Exact baseline — no noise, no adversary |
| Backend noise model | ~45% | 33× overestimate — not a valid hardware proxy |
| IBM Hardware (ibm_kingston, N=27) | 1.19% ± 0.57% | Real device noise floor |
| Synthetic attack (p_flip=0.25) | 25.56% ± 0.97% | Bitstring-level bit flips |
| KS statistic | 1.0 | p = 1.45×10⁻¹¹ — fully separable distributions |

**The noise model finding:** Backend-derived noise models produce ~45% QBER on BB84, while real hardware gives ~1.19%. The overestimation occurs because BB84 circuits are only 2–4 gates deep after transpilation. The noise model applies full-device calibration error budgets (derived from benchmark circuits of depth ~10) regardless of circuit depth, so it accumulates errors that never actually occur on a shallow circuit. Noise models are treated as stress-test upper bounds only.

**The scaling finding:** Detection sensitivity depends on qubit count and trial count simultaneously. At N=27 with 20 trials on ibm_kingston, detection is clean (KS=1.0). At N=36, 20 trials fails — 50 trials are needed for marginal detection (KS=0.28, p=0.039). At N=54, detection fails even at 50 trials due to qubit calibration heterogeneity: as qubit count grows, the transpiler assigns circuits to qubits spanning a wider range of calibration quality, driving up QBER variance. Note: BB84 has no two-qubit gates, so SWAP overhead plays no role — variance growth is entirely due to qubit quality spread.

---

## Iteration Status

**Iteration 1 — Complete**
Ideal BB84 on AerSimulator vs intercept-resend attack modelled as a Pauli channel. Confirmed QBER = 0% (ideal) and ≈ 25% (attack). Validated circuit logic, sifting, and QBER estimator.

**Iteration 2 — Complete**
Multi-trial comparison across ideal simulator, backend noise model, and IBM hardware. Discovered the 33× noise model overestimation. Hardware QBER consistently ~0.6%–1.4%.

**Iteration 3 — Complete**
Full distinguishability analysis: 20-trial hardware baseline, bitstring-level synthetic attack, Wilson confidence intervals, t-test and KS-test. Key reconciliation and privacy amplification verified end-to-end. Scaling study from N=27 to N=54 across ibm_kingston, ibm_fez, and ibm_marrakesh.

---

## Repository Structure

```
├── bb84_research.py          ← Single consolidated research script (all iterations)
├── bb84_iteration1.py        ← Standalone Iteration 1 script (AerSimulator only)
├── Key_sharing.ipynb         ← Development notebook (scratch work, all iterations)
├── results/
│   ├── hw_trials_with_attack.json         ← ibm_kingston 20-trial baseline + attack
│   ├── statistical_results.json           ← t-test, KS-test, Wilson CIs
│   ├── two_backend_comparison.json        ← kingston vs marrakesh comparison
│   ├── hw_threshold_validated.json        ← 2% threshold on real bitstrings
│   ├── scaling_and_reconciliation.json    ← N=27 and N=54 with reconciliation
│   ├── scaling_breakdown.json             ← N=36 and N=45 scaling study
│   ├── session2_N36_kingston_50t.json     ← N=36 ibm_kingston 50 trials
│   ├── reconstructed_all_data.json        ← Complete consolidated dataset
│   └── fine_sweep.json                    ← Partial attack sweep (1%–10% Eve)
└── README.md
```

The `.py` files are the primary research scripts. The notebook is scratch work kept for full reproducibility.

---

## Running the Code

**Install dependencies:**
```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime numpy scipy matplotlib
```

**Iteration 1 — local simulation, no hardware needed:**
```bash
python bb84_research.py --mode iter1
```

**Hardware execution:**
```bash
# Set token — never hardcode it
export IBM_QUANTUM_TOKEN=your_token_here     # Mac/Linux
set IBM_QUANTUM_TOKEN=your_token_here        # Windows

# Run 20 trials on ibm_kingston, 27 qubits
python bb84_research.py --mode hardware --n-qubits 27 --shots 512 --trials 20 --pin ibm_kingston

# Run analysis on saved results
python bb84_research.py --mode analysis --results results/hw_trials_with_attack.json
```

**In Jupyter — call functions directly:**
```python
import os
os.environ["IBM_QUANTUM_TOKEN"] = "your_token_here"

from bb84_research import (
    run_sanity_checks,
    run_iteration1,
    run_hardware_multi_trial,
    ExperimentConfig,
    HardwareConfig,
)

# Sanity checks
run_sanity_checks()

# Iteration 1
result = run_iteration1(ExperimentConfig())

# Hardware run
cfg    = HardwareConfig(n_qubits=27, shots=512, p_flip=0.005)
result = run_hardware_multi_trial(cfg, n_trials=20,
                                   token=os.environ["IBM_QUANTUM_TOKEN"],
                                   pin_name="ibm_kingston")
```

---

## Experimental Design

### BB84 Circuit

Alice prepares each qubit in one of four states (Z-basis: |0⟩ or |1⟩, X-basis: |+⟩ or |−⟩). Bob measures in a randomly chosen basis. Only positions where bases match are kept (sifting, ~50% retention). A subset of sifted bits is publicly compared to estimate QBER; the remainder forms the secret key.

### Attack Model

The intercept-resend attack is modelled as a Pauli channel on `id` marker gates inserted between Alice's preparation and Bob's measurement:

```
ρ → 0.50·IρI + 0.25·XρX + 0.25·ZρZ
```

This is statistically equivalent to Eve measuring in a random basis and re-sending. Expected QBER ≈ 25% on the sifted key.

For hardware runs, a synthetic post-measurement attack is applied: bits in the raw hardware counts are flipped independently with probability `p_flip`. This models the observable effect of channel tampering without requiring mid-circuit quantum interception.

### Check/Secret Split

All QBER estimation uses only the **check bit subset** (20% of sifted bits by default). The remaining 80% is retained as the secret key — never revealed. This follows the BB84 specification. Experiments using all sifted bits for checking leave no secret key and are methodologically incorrect.

### Key Reconciliation

Parity-based reconciliation (simplified Cascade pass 1) corrects disagreements between Alice and Bob's secret key bits. Privacy amplification using SHA-256 then reduces the key length by the number of parity bits publicly revealed, removing any information an eavesdropper could have obtained.

---

## Hardware Backends Used

| Backend | Qubits | Used for |
|---|---|---|
| ibm_kingston | 156 | Primary baseline, scaling study, session 2 |
| ibm_fez | 156 | Iterations 2 & 3, scaling study |
| ibm_marrakesh | 156 | Two-backend comparison |

---

## Scaling Study Summary

| Config | N | Trials | HW mean QBER | KS | Detect 2% Eve? |
|---|---|---|---|---|---|
| ibm_kingston | 27 | 20 | 1.19% | 1.00 | YES |
| ibm_fez | 27 | 50 | 1.66% | 0.32 | YES |
| ibm_fez | 36 | 50 | 1.85% | 0.34 | YES |
| ibm_kingston | 36 | 50 | 1.53% | 0.28 | YES (marginal) |
| ibm_kingston | 36 | 20 | 1.88% | 0.35 | NO |
| ibm_kingston | 45 | 20 | 1.26% | 0.35 | NO |
| ibm_fez | 54 | 50 | 2.90% | 0.24 | NO |

Detection requires 50 trials at N=36. At N=54, qubit calibration heterogeneity prevents detection even at 50 trials — SWAP count is zero at all qubit counts, so routing is not the cause. One trial (seed 61, N=54) produced hardware QBER = 25.6% — identical to a full attack — from hardware noise alone.

---

## References

- Bennett & Brassard (1984) — BB84 protocol
- Shor & Preskill (2000) — Security proof
- [IBM Quantum Documentation](https://docs.quantum.ibm.com)
- [Qiskit Aer Documentation](https://qiskit.github.io/qiskit-aer)
