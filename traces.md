# Source traces for the top flags

Gathered with **Valency MCP Bond** (through Claude Code) and, where Bond couldn't reach the
source, by reading the original paper. Each flag is checked against the paper it cites.

| # | Flag (audit output) | Trace | Verdict |
|---|---|---|---|
| 1 | Nd0.25Li0.25TaO3, Liverpool 1.91e-6 vs OBELiX 1.31e-8 S/cm, resid +2.16, *unexplained; nearest S/m stored as S/cm (×100), off by 0.16* | Source: Mizumoto & Hayashi, *Solid State Ionics* 116 (1999) 263, 10.1016/S0167-2738(98)00414-7. **Not in Bond's corpus**; read from the PDF. The paper reports σ in **S m⁻¹** and plots σT in S m⁻¹ K; room-temperature Nd is ≈1e-8 S cm⁻¹ from its Figs. 3–4. | **Liverpool error, ×100 (S/m stored as S/cm).** Matches the case Wang et al. (arXiv 2609.01621) found by hand. |
| 2 | Li6.5La3Zr1.75Te0.25O12 and Li6.75La3Zr1.875Te0.125O12, Liverpool ≈10× below OBELiX, *S/m vs mS/cm (×10)* | Source: Deviannapoorani et al., *J. Power Sources* 240 (2013) 18, 10.1016/j.jpowsour.2013.03.166, read from the PDF. Table 2 (30 °C): 1.02e-3 and 3.30e-4 S cm⁻¹, which equal OBELiX. | **Liverpool error**, but ≈7–9× after correcting to 25 °C, not a clean ×10. The "×10" label is a near-miss; the honest cause is *unknown*. |
| 3 | AlCoCrFeNiTi0.5, MPEA YS 2260 MPa with HV 178, *unexplained* (hardness vs yield strength) | Source: Zhou et al., *APL* 90, 181904 (2007), 10.1063/1.2734517, read from the PDF. Reports YS 2.26 GPa (compression); **reports no hardness**. | **MPEA error: HV not supported by the cited source** (provenance). |
| 4 | Li3PS4, Liverpool 1.6e-4 vs OBELiX 2.6e-7 / 8.9e-7 S/cm, resid +2.3 to +2.8, *unexplained* | **Bond:** Liu et al., *JACS* 2013, 10.1021/ja3110895 (880 citations): nanoporous **β**-Li3PS4 raises room-temperature σ **by 3 orders of magnitude** over bulk. Bond also found Yang et al., *ACS AMI* 2016 (10.1021/acsami.6b06754), confirming 1.64e-4 S cm⁻¹ for nanoporous β. | **Not an error: two different phases (nanoporous β vs bulk γ) from the same paper**, stored under one composition. A real limitation: matching by composition alone can't tell polymorphs apart. |
| 5 | Sm0.52Li0.38TiO2.97, Liverpool 1.5e-3 vs OBELiX 2.0e-7, resid +3.9, *unexplained* | Source 10.1016/0167-2738(94)90310-7 (*Solid State Ionics* 1994). **Not in Bond's corpus**; paper not yet read. A 7,500× gap fits no single factor; ×1000 plus a temperature/phase mismatch is possible. | **Open.** Needs the paper. |

**ChemRxiv re-check (2026-10-21):** Bond added ChemRxiv (57k preprints, 2017 onwards). Re-searching the open
flags (Sm-Li titanate, Li4B7O12Cl) found only unrelated recent electrolyte preprints; their sources (1977, 1994)
predate ChemRxiv, so case 5 stays open.

**Bond coverage note:** Bond (PubMed + arXiv + bioRxiv/medRxiv + others) found the *JACS* and *ACS*
sources instantly but not older *Solid State Ionics* papers (cases 1 and 5). Tracing those needs
publisher access.
