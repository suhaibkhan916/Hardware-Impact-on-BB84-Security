# BB84 QKD — Hardware Impact on Security

Experimental evaluation of the BB84 Quantum Key Distribution protocol on IBM Quantum hardware. The core question is whether natural NISQ device noise can be mistaken for an adversarial intercept-resend attack, and if not, where the detection boundary is.

---

## Research Question

BB84 guarantees that any eavesdropper disturbs the quantum channel in a detectable way. On real superconducting hardware, the device itself introduces errors. This project asks: are those hardware errors small enough that Alice and Bob can still reliably detect an attacker, and if so, under what conditions?

---

## Key Results

| Mode | QBER | Notes |
|---|---|---|
| Ideal simulator | 0.00% | Exact baseline — no noise, no adversary |
| Backend noise model | ~45% | 33× overestimate — not a valid hardware proxy |
| IBM Hardware (ibm_kingston, N=27) | 1.37% ± 0.50% | Real device noise floor |
| IBM Hardware (ibm_kingston, N=36, 44 trials) | 0.896% ± 0.123% | Latest dataset — recovered from job history |
| Synthetic attack (full intercept) | 25.56% ± 0.97% | Equivalent to Eve in channel |
| KS statistic (N=27, 20 trials) | 1.0 | p = 1.45×10⁻¹¹ — fully separable |
| KS statistic (N=36, 44 trials, 10% Eve) | 0.18 | p = 0.465 — indistinguishable |

**The noise model finding:** Backend-derived noise models produce ~45% QBER on BB84 while real hardware gives ~1.37%. The overestimation occurs because BB84 circuits are only 2–4 gates deep after transpilation. The noise model applies full-device calibration error budgets regardless of circuit depth, so it accumulates errors that never actually occur on a shallow circuit. Noise models are treated as stress-test upper bounds only.

**The scaling finding:** Detection sensitivity depends on qubit count and trial count simultaneously. At N=27 with 20 trials on ibm_kingston, detection is clean (KS=1.0). At N=36, 20 trials fails — 50 trials are needed for marginal detection (KS=0.28, p=0.039). At N=54, detection fails even at 50 trials due to noise variance growth.

**The seed 61 finding:** At ibm_fez, N=54, seed 61, hardware QBER reached 25.6% with no eavesdropper present — statistically indistinguishable from a full intercept-resend attack. This is the central empirical finding: hardware noise alone can mimic a full attack on NISQ devices.

**The low-intercept indistinguishability finding:** In the 44-trial ibm_kingston experiment at N=36, a 10% Eve intercept fraction produced a QBER distribution statistically indistinguishable from the hardware baseline (KS=0.18, p=0.465). This confirms that partial attacks below a certain threshold cannot be detected against the hardware noise floor.

**The finite-key crossover:** Asymptotic Shor–Preskill key rate is invalid at small N. With composability parameters ε_PA = ε_EC = 10⁻¹⁰ and 20% check fraction, the finite-key rate becomes positive only at n_sifted ≥ 305 bits — approximately 610 physical qubits at 50% retention. All experiments in this work lie in the zero-rate region by design: this is a detection-sensitivity study, not a key-generation study.

---

## Iteration Status

**Iteration 1 — Complete**
Ideal BB84 on AerSimulator vs intercept-resend attack modelled as a Pauli channel. Confirmed QBER = 0% (ideal) and ≈ 25% (attack). Validated circuit logic, sifting, and QBER estimator.

**Iteration 2 — Complete**
Multi-trial comparison across ideal simulator, backend noise model, and IBM hardware. Discovered the 33× noise model overestimation. Hardware QBER consistently ~0.6%–1.4%.

**Iteration 3 — Complete**
Full distinguishability analysis: multi-trial hardware baseline, bitstring-level synthetic attack, Wilson confidence intervals, t-test and KS-test. Key reconciliation and privacy amplification verified end-to-end. Scaling study from N=27 to N=54 across ibm_kingston, ibm_fez, and ibm_marrakesh.

**Iteration 4 — Complete**
Synthetic attack equivalence formally verified, finite-key analysis with hardware recommendation, pipeline verification on full 44-trial dataset, and metadata-free QBER reconstruction from raw circuit counts.

---

## Repository Structure

```
├── bb84_research.py                    ← Single consolidated research script (all iterations)
├── bb84_iteration1.py                  ← Standalone Iteration 1 script (AerSimulator only)
├── Key_sharing.ipynb                   ← Development notebook
├── finite_key_analysis.py              ← Finite-key crossover analysis
├── synthetic_attack_equivalence.py     ← Physical vs synthetic attack verification
├── pipeline_verification.py            ← Full reconciliation + privacy amplification on real data
├── retrieve_jobs.py                    ← Pull completed jobs from IBM Quantum platform (no QPU cost)
│
├── results/                            ← All JSON outputs
│   ├── hw_trials_with_attack.json         ← ibm_kingston 20-trial baseline + attack
│   ├── statistical_results.json           ← t-test, KS-test, Wilson CIs
│   ├── two_backend_comparison.json        ← kingston vs marrakesh comparison
│   ├── hw_threshold_validated.json        ← 2% threshold on real bitstrings
│   ├── scaling_and_reconciliation.json    ← N=27 and N=54 with reconciliation
│   ├── scaling_breakdown.json             ← N=36 and N=45 scaling study
│   ├── session2_N36_kingston_50t.json     ← N=36 ibm_kingston 50 trials
│   ├── reconstructed_all_data.json        ← Complete consolidated dataset
│   ├── fine_sweep.json                    ← Partial attack sweep (1%–10% Eve)
│   ├── per_circuit_counts.json            ← Raw per-circuit counts (44 paired trials)
│   ├── final_bb84_analysis.json           ← QBER from Z-basis reconstruction
│   ├── finite_key_summary.json            ← Finite-key crossover results
│   ├── synthetic_attack_equivalence.json  ← 1200-trial equivalence verification
│   └── pipeline_results.json              ← Per-trial reconciliation + key agreement
│
├── graphs/                             ← All plots and figures
│   ├── bb84_final_results_publication.png ← Main results (per-trial QBER, histogram, delta)
│   ├── finite_key_analysis.png            ← Crossover at n_sifted = 305
│   ├── synthetic_attack_equivalence.png   ← Physical vs synthetic match across all f
│   ├── plot_calibration_aware_N36.png     ← Calibration-aware qubit selection
│   ├── plot_swap_overhead.png             ← SWAP overhead analysis
│   ├── plot_secret_key_rate_analysis.png  ← Secret key rate across configs
│   ├── plot_scaling_mechanism.png         ← Heterogeneity-driven scaling
│   ├── plot_noise_model_corrected.png     ← 33× overestimation derivation
│   └── publication_grade_bb84_corrected.png ← Publication-grade summary figure
│
└── README.md
```

The `.py` files are the primary research scripts. The notebook is scratch work kept for full reproducibility. All numerical outputs go to `results/` and all figures to `graphs/`.

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

# Analysis on saved results
python bb84_research.py --mode analysis --results results/hw_trials_with_attack.json
```

**Retrieve completed jobs from IBM platform (no QPU cost):**
```bash
# Use this when QPU quota is exhausted but jobs already ran
python retrieve_jobs.py
# → produces results/per_circuit_counts.json with raw counts for every circuit in every job
```

**Local analysis scripts (no QPU access needed):**
```bash
# Finite-key crossover analysis
python finite_key_analysis.py
# → graphs/finite_key_analysis.png, results/finite_key_summary.json

# Synthetic vs physical attack equivalence (AerSimulator only)
python synthetic_attack_equivalence.py
# → graphs/synthetic_attack_equivalence.png, results/synthetic_attack_equivalence.json

# Full BB84 pipeline on existing hardware data
python pipeline_verification.py
# → results/pipeline_results.json with per-trial reconciliation and key agreement
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

The intercept-resend attack is implemented at circuit level: Eve applies a random-basis rotation pair (H or identity, depending on her chosen basis) with a barrier-isolated identity gate between them, followed by a mid-circuit measurement, reset, and conditional re-preparation. This is mathematically equivalent to Eve physically measuring and re-sending.

For analysis purposes, the attack QBER follows the standard BB84 prediction:
```
QBER_attack ≈ QBER_hw + (f/4)·(1 − 2·QBER_hw)
```
where f is the intercept fraction. Equivalence between this circuit-level implementation and a classical "Eve in channel" model has been verified empirically (`synthetic_attack_equivalence.py`) across f ∈ {0.0, 0.1, 0.25, 0.5, 0.75, 1.0} with KS p > 0.05 in all cases.

### Check/Secret Split

All QBER estimation uses only the **check bit subset** (20% of sifted bits by default). The remaining 80% is retained as the secret key — never revealed. This follows the BB84 specification. Experiments using all sifted bits for checking leave no secret key and are methodologically incorrect.

### Key Reconciliation

Parity-based reconciliation (simplified Cascade pass 1) corrects disagreements between Alice and Bob's secret key bits. Privacy amplification using SHA-256 then reduces the key length by the number of parity bits publicly revealed, removing any information an eavesdropper could have obtained.

### Metadata-Free QBER Reconstruction

When the original (alice_bit, alice_basis, bob_basis) metadata is unavailable (e.g. when retrieving jobs after a script crash), QBER can still be reconstructed from raw circuit counts using the bimodal p(1) distribution: circuits with p(1) < 0.3 are Z-basis with alice = 0 (error rate = p(1)), circuits with p(1) > 0.7 are Z-basis with alice = 1 (error rate = 1 − p(1)), and circuits with 0.3 ≤ p(1) ≤ 0.7 are X-basis and discarded (not sifted in BB84). This approach is valid for well-calibrated hardware where the bimodal structure is preserved.

### Finite-Key Framework

The asymptotic Shor–Preskill rate `r = 1 − 2·h(QBER)` is only valid for n_sifted → ∞. For real trial sizes, the finite-key rate includes Hoeffding statistical uncertainty on QBER plus composability penalties for privacy amplification and error correction:
```
r_finite = (n_secret / n_sifted)·[1 − h(QBER + δ) − h(QBER)]
           − (log₂(2/ε_PA) + log₂(1/ε_EC)) / n_sifted
```
With ε_PA = ε_EC = 10⁻¹⁰ and 20% check fraction, r_finite becomes positive at n_sifted ≥ 305 bits (~610 physical qubits at 50% sifting retention). All experiments in this work lie below this threshold by design.

---

## Hardware Backends Used

| Backend | Qubits | Used for |
|---|---|---|
| ibm_kingston | 156 | Primary baseline, scaling study, session 2, 44-trial confirmation |
| ibm_fez | 156 | Iterations 2 & 3, scaling study, seed 61 anomaly |
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
| ibm_kingston | 36 | 44 | 0.896% | 0.18 | NO (at 10% Eve) |
| ibm_kingston | 45 | 20 | 1.26% | 0.35 | NO |
| ibm_fez | 54 | 50 | 2.90% | 0.24 | NO |

Detection requires 50 trials at N=36. At N=54, noise accumulation prevents detection even at 50 trials. One trial (seed 61, N=54) produced hardware QBER = 25.6% — identical to a full attack — from hardware noise alone.

---

## Pipeline Verification

The complete BB84 pipeline (sifting → check-bit QBER → parity reconciliation → SHA-256 privacy amplification → key agreement) was executed on all 44 paired hardware trials from the latest ibm_kingston session. Results:

- Valid trials processed: **44/44**
- Mean sifted bits per trial: 18.1
- Mean secret bits per trial: 14.9
- Reconciliation success rate: **44/44 = 100%**
- Final key agreement (Alice = Bob): **44/44 = 100%**

This confirms that every protocol stage operates correctly on real hardware noise within the regime studied. The mean final key length (14.9 bits) is below the cryptographic threshold and is reported here for pipeline validation only; the finite-key analysis above quantifies the hardware scale required for composable key generation.

---

## References

- Bennett & Brassard (1984) — BB84 protocol
- Shor & Preskill (2000) — Asymptotic security proof
- Scarani & Renner (2008) — Finite-key framework
- Hoeffding (1963) — Probability inequalities for bounded variables
- Lo, Curty, Tamaki (2014) — Secure QKD review
- [IBM Quantum Documentation](https://docs.quantum.ibm.com)
- [Qiskit Aer Documentation](https://qiskit.github.io/qiskit-aer)
