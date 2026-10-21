# LitAudit: catching the hidden errors in the databases AI for materials learns from

**Shivasish Mishra** · OSI Hackathon 2026 (Bochum hub) · code: https://github.com/shivasish-mishra/litaudit

**Problem.** Materials ML models are trained on databases built from values copied out of papers. These
databases carry *structured* errors: unit and quantity mix-ups (S/m stored as S/cm, σT stored as σ,
MPa vs GPa) that shift a value by a fixed factor yet leave it physically plausible, so ordinary
outlier filters miss them. Wang et al. (arXiv 2609.01621, 2026) traced one such 100× error into a public
Li-ion conductivity database *by hand*.

**What LitAudit does.** For every value it gathers independent references and diagnoses any disagreement:
1. **Another database**: the same paper and composition (normalised to atom fractions) in a second database, at about the same temperature.
2. **A physics relation**: hardness vs yield strength (Tabor, calibrated on the data) and measured vs rule-of-mixtures density.
3. **Diagnosis**: the gap in log space is matched against a per-property library of known factors (×10/×100/×1000, ×≈298 for σT vs σ, ×6.9 ksi, ×9.8/×102 hardness units). Output: *agree*, a *named factor*, or *unexplained* plus the nearest factor and how far off it is. No auto-relabelling.
4. **Trace**: flagged entries are traced to their source with **Valency MCP Bond** or by reading the paper.

Adding a property means adding its units and relations; the code is unchanged. Shown on two unrelated
domains: Li-ion conductivity (Liverpool, 820 entries; OBELiX, 599) and high-entropy-alloy mechanical
properties (MPEA, 1,545 rows).

![LitAudit figure](figures/litaudit.png)
*A: 128 entries present in both conductivity databases; 110 agree within 0.3 dex. B: hardness vs yield strength for 224 alloys. C: planted unit errors recovered by name (every planted error was flagged).*

**Results.** 464 comparisons; 35 flagged. Every flag we checked against the original paper was explained:

| Flag | Original paper says | Verdict |
|---|---|---|
| Nd₀.₂₅Li₀.₂₅TaO₃: Liverpool 1.9×10⁻⁶ vs OBELiX 1.3×10⁻⁸ S/cm (nearest factor: ×100) | σ reported in **S/m**; room-temperature value ≈10⁻⁸ S/cm | **Liverpool ×100 error** (S/m stored as S/cm). Same case as Wang et al., found automatically |
| Te-doped LLZO (2 entries): Liverpool ≈10× below OBELiX | Table 2 matches OBELiX exactly | **Liverpool error**, ≈7–9× (cause unknown; "×10" label is a near-miss) |
| AlCoCrFeNiTi₀.₅: YS 2260 MPa with HV 178 | YS 2.26 GPa; **no hardness reported** | **MPEA provenance error**: value not in the cited source |
| Li₃PS₄: Liverpool 1.6×10⁻⁴ vs OBELiX ≈10⁻⁷ S/cm (Bond trace) | Nanoporous β-phase is 1000× more conductive than bulk γ | **Not an error**: two phases under one composition (a limitation, correctly left "unexplained") |

**Planted-error benchmark** (each factor injected into agreeing comparisons): conductivity and density unit
errors are named correctly **94–100%** of the time. Hardness/yield errors are **always flagged** but named only
40–63% of the time, because that relation is intrinsically ~0.3 dex noisy.

**Limitations.** Only one real case from the published ground truth (Wang et al.) is in an open database; most numbers
come from planted errors. Composition matching can't separate polymorphs or processing routes. Bond
didn't cover older *Solid State Ionics* papers, so those traces needed the PDF. Tolerances (0.3 dex agreement,
0.1 dex factor match) were not tuned on the verified cases; the Nd case is left "unexplained" (0.16 off) rather than forced.

**Impact.** Literature-derived databases are infrastructure for AI-driven materials discovery. LitAudit gives
curators and model builders a cheap, explainable audit: *which* entries disagree, *why* (when a known
factor fits), and *where to look* (the source). It found three real errors in one morning in two public
databases, and the same code applies to any property with known units and relations.

*Data: Liverpool Li-ion database (Hargreaves et al. 2023, academic licence, not redistributed), OBELiX
(CC-BY 4.0), MPEA (Borg et al. 2020, Apache 2.0). Builds on those datasets; all audit code is new.*
