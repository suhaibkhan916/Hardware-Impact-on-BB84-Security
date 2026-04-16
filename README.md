# BB84 QKD — Circuit-Level Experimental Evaluation

**Research framework for evaluating the BB84 Quantum Key Distribution protocol under hardware noise and adversarial disturbance.**

---

## Overview

This project implements a **research-grade, circuit-level experimental framework** for the BB84 protocol using Qiskit AerSimulator and IBM Quantum hardware. The central scientific question is:

> *Can natural hardware noise be mistaken for an adversarial intercept–resend attack — and if not, what QBER thresholds reliably distinguish the two?*

This is a **cryptographic evaluation framework**, not a production QKD deployment. All claims are scoped to circuit-level simulation and NISQ hardware execution.

---

## Project Status

| Iteration | Status | Description |
|-----------|--------|-------------|
| Iteration 1 | ✅ Complete | Ideal baseline + Intercept–Resend attack (AerSimulator) |
| Iteration 2 | ✅ Complete | Multi-trial comparative study (Ideal vs Noisy Sim vs Hardware) |
| Iteration 3 | 🔄 In Progress | Distinguishability analysis — noise vs adversarial disturbance |

---

## Key Findings (Iterations 1 & 2)

| Mode | Observed QBER | Interpretation |
|------|---------------|----------------|
| Ideal simulator | ~0% | Correct baseline — zero error in noise-free execution |
| IBM Hardware | ~0.6% | Low, stable device noise |
| Backend noisy simulator | ~45% | **Unrealistically pessimistic** — not a valid proxy for hardware |
| Intercept–resend attack | ~25% | Consistent with BB84 theoretical prediction |

**Critical insight:** Backend-derived noise models significantly overestimate error rates for shallow BB84 circuits. Real hardware is the ground truth. Noisy simulators are treated only as stress-test upper bounds.

---

## Repository Structure

```
project_root/
│
├── bb84_iteration1.py       ← Iteration 1 main script (this file)
│
├── src/                     ← (future) shared library modules
│   ├── __init__.py
│   ├── protocol.py          ← BB84 core logic
│   ├── noise.py             ← Noise and attack models
│   └── metrics.py           ← QBER estimation and reporting
│
├── experiments/             ← (future) per-iteration scripts
│   ├── iter1_ideal_aer.py
│   ├── iter2_multi_trial.py
│   └── iter3_distinguishability.py
│
├── tests/                   ← (future) unit and integration tests
│   └── test_bb84_core.py
│
├── notebooks/               ← Jupyter scratch notebooks (not primary source)
│   ├── AER.ipynb
│   ├── Key_sharing.ipynb
│   └── NEW_Method.ipynb
│
├── results/                 ← Saved JSON metrics outputs
│
├── README.md                ← This file
└── ANALYSIS.md              ← Code analysis and roadmap
```

---

## Iteration 1 — Experimental Design

### Execution Modes

**Mode 1 — Ideal Baseline**
- AerSimulator, stabilizer method
- No noise model, no adversary
- Expected QBER ≈ 0%
- Purpose: verify circuit logic correctness

**Mode 2 — Intercept–Resend Attack**
- AerSimulator with Eve-equivalent Pauli channel
- Channel: ρ → 0.50·IρI + 0.25·XρX + 0.25·ZρZ
- Applied via `id` marker gates inserted between Alice prep and Bob measurement
- Expected QBER ≈ 25% (as established in BB84/QKD foundational literature)

### Why this channel models Eve

Eve picks a random basis (Z or X) with equal probability. When her basis matches Alice's (prob = 0.5), no error occurs. When it does not match (prob = 0.5), the re-sent state introduces errors in the mismatched basis — producing a net QBER of 25% on the sifted key.

---

## Running the Code

### Requirements

```bash
pip install qiskit qiskit-aer numpy matplotlib
```

Tested with:
- Python 3.10+
- Qiskit ≥ 1.0
- Qiskit-Aer ≥ 0.14

### Run Iteration 1

```bash
python bb84_iteration1.py
```

### Expected Output

```
============================================================
BB84 QKD — Iteration 1: Ideal + Intercept–Resend
============================================================

Running sanity checks ...
  [PASS] Ideal QBER < 2%
         Ideal QBER = 0.0000
  [PASS] Intercept–resend QBER > 10%
         IR QBER    = 0.2471
  [PASS] Sifting retention ≈ 50%
         Retention  = 0.5117
Sanity checks passed.

Running ideal BB84 simulation ...
Running intercept–resend simulation ...

============================================================
RESULTS
============================================================
{
  "iteration": 1,
  "ideal": {
    "mode": "ideal",
    "n_qubits": 256,
    "shots": 4096,
    "QBER": 0.0,
    ...
  },
  "intercept_resend": {
    "mode": "intercept_resend",
    "QBER": 0.25,
    ...
  }
}

DISTINGUISHABILITY ANALYSIS
  Ideal QBER           : 0.0000
  Intercept–Resend QBER: 0.2500
  ΔQBER (IR - Ideal)   : 0.2500
  [CONCLUSION] Adversarial QBER is statistically distinguishable
               from ideal hardware noise. BB84 would detect Eve.
```

### Metrics Schema

Each experiment produces a structured output:

```json
{
  "mode": "ideal | intercept_resend",
  "n_qubits": 256,
  "shots": 4096,
  "seed": 42,
  "backend_name": "AerSimulator(stabilizer)",
  "disturbance_type": "none | intercept_resend_equivalent_channel",
  "raw_key_length": 256,
  "sifted_key_length": 131,
  "retention_rate": 0.5117,
  "sample_size": 64,
  "errors_in_sample": 0,
  "QBER": 0.0
}
```

---

## Scientific Framing

This work is a **circuit-level experimental cryptographic evaluation** under controlled simulation. Specifically:

- Hardware-first: IBM Quantum hardware results are the physical ground truth.
- Noisy simulators: treated as stress-test upper bounds only, not hardware proxies.
- Adversarial models: intercept–resend is implemented as a statistically equivalent Pauli channel, not real-time physical interception.
- Claims are scoped to: QBER estimation, distinguishability analysis, and statistical comparison across modes.

This project does **not** claim:
- Production-ready QKD
- Absolute cryptographic security guarantees
- Real-world photonic channel performance

---

## Architecture Principles

- **No global state.** All configuration passed through `ExperimentConfig`.
- **Reproducibility.** Every RNG call uses explicit seeds.
- **Modular.** Every logical step is its own function with type hints and docstrings.
- **Stabilizer simulation.** BB84 uses only Clifford gates; the stabilizer method is exact and efficient.
- **Mandatory sanity checks.** `run_sanity_checks()` is always called before the main experiment.

---

## Roadmap

### Iteration 3 (Next)

- [ ] Hardware baseline execution on IBM Quantum
- [ ] Synthetic post-measurement attack (bit flips, p=0.25) on hardware output
- [ ] Statistical hypothesis testing (t-test or KS-test) across modes
- [ ] Confidence intervals on QBER estimates
- [ ] Multi-trial evaluation (multiple seeds)
- [ ] QBER threshold estimation (empirical security boundary)

### Future

- [ ] Error mitigation techniques (ZNE, measurement error mitigation)
- [ ] Adaptive adversarial models
- [ ] Real-time QBER monitoring
- [ ] Extension to E91 and B92 protocols

---

## Security Notice

**Never commit IBM Quantum API keys to version control.**

Use environment variables:

```python
import os
from qiskit_ibm_runtime import QiskitRuntimeService

QiskitRuntimeService.save_account(
    channel="ibm_cloud",
    token=os.environ["IBM_QUANTUM_TOKEN"],
    set_as_default=True,
    overwrite=True,
)
```

Add `.env` and any file containing `ApiKey-` to `.gitignore`.

---

## References

- Bennett & Brassard, "Quantum cryptography: Public key distribution and coin tossing," 1984.
- Shor & Preskill, "Simple proof of security of the BB84 quantum key distribution protocol," 2000.
- IBM Quantum Documentation: [docs.quantum.ibm.com](https://docs.quantum.ibm.com)
- Qiskit Aer Documentation: [qiskit.github.io/qiskit-aer](https://qiskit.github.io/qiskit-aer)
