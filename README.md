# BB84 QKD — Hardware Impact on Security

Experimental evaluation of the BB84 Quantum Key Distribution protocol on IBM Quantum hardware. The core question is whether natural device noise on real superconducting hardware can be mistaken for an eavesdropping attack, and if not, where the line is.

---

## What This Project Is

BB84 is the foundational QKD protocol. In theory, any eavesdropper disturbs the quantum channel in a way that Alice and Bob can detect by measuring the Quantum Bit Error Rate (QBER). In practice, real quantum hardware introduces its own errors — and the question is whether those errors are small enough that you can still tell the difference between a noisy device and an active attack.

This project runs BB84 across four conditions — ideal simulation, noisy simulation, real IBM hardware, and hardware with a simulated attack — and compares the QBER across all of them.

---

## Key Results So Far

| Mode | QBER | Notes |
|------|------|-------|
| Ideal simulator | ~0% | Expected — no noise, no adversary |
| IBM Hardware | ~0.6% | Low and stable, real device noise |
| Backend noise model | ~45% | Far too high — not a reliable proxy for hardware |
| Intercept–resend attack | ~25% | Matches BB84 theory |

The backend noise model result (~45%) is the most important finding so far. Noise models are built from gate calibration data, but BB84 circuits are so shallow (depth 2–3 after transpilation) that almost no gates execute — so the noise never accumulates the way the model predicts. This means you cannot use a noisy simulator to approximate real hardware for this protocol. Hardware runs are the only reliable reference.

---

## Project Structure

```
├── bb84_iteration1.py      # Ideal + intercept–resend simulation (Aer)
├── bb84_hardware.py        # Hardware execution + synthetic attack (IBM Quantum)
├── AER.ipynb               # Development notebook for Iteration 1
├── Key_sharing.ipynb       # Early BB84 key sharing exploration
├── NEW_Method.ipynb        # Alternative circuit approach scratch work
└── README.md
```

The `.py` files are the primary research scripts. The notebooks are scratch work kept for reference.

---

## Iteration Status

**Iteration 1 — Done**
Ran ideal BB84 on AerSimulator and compared it against an intercept–resend attack modelled as a Pauli channel. Confirmed QBER ≈ 0% (ideal) and ≈ 25% (attack). Validated the circuit logic, sifting pipeline, and QBER estimator.

**Iteration 2 — Done**
Multi-trial comparison across ideal sim, backend noise model, and real IBM hardware. This is where the noise model issue was discovered. Hardware QBER was consistently ~0.6%, backend model was ~45%.

**Iteration 3 — In Progress**
The focus shifts to distinguishability: can you statistically prove that an attack is happening, given that hardware always has some background noise? This requires multi-trial data, hypothesis testing, and confidence intervals — none of which are in the codebase yet.

---

## Running the Code

Install dependencies:
```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime numpy matplotlib
```

**Iteration 1 (local, no hardware needed):**
```bash
python bb84_iteration1.py
```

**Hardware execution:**

Set your IBM Quantum token as an environment variable, then run:
```bash
# Windows
set IBM_QUANTUM_TOKEN=your_token_here

# Mac / Linux
export IBM_QUANTUM_TOKEN=your_token_here

python bb84_hardware.py
```

Or in a Jupyter notebook, set it in a cell before running:
```python
import os
os.environ["IBM_QUANTUM_TOKEN"] = "your_token_here"
```

Configuration (n_qubits, shots, seed, channel) is set at the top of `main()` in each script — edit the variables directly.

---

## What Still Needs to Be Done

- Multi-trial runner (loop over seeds, collect QBER distributions)
- Statistical hypothesis testing — t-test and KS-test between noise and attack distributions
- Confidence intervals on QBER estimates
- Empirical QBER threshold from hardware data (currently stated as 5–15%, needs measurement)
- Distribution plots across trials (not just single-run bar charts)

---

## References

- Bennett & Brassard, 1984 — original BB84 paper
- Shor & Preskill, 2000 — security proof
- [IBM Quantum Documentation](https://docs.quantum.ibm.com)
