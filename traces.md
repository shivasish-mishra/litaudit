# Source traces for the top flags

Gathered with **Valency MCP Bond** (through Claude Code) and, where Bond couldn't reach the
source, by reading the original paper. Each flag is checked against the paper it cites.

| # | Flag (audit output) | Trace | Verdict |
|---|---|---|---|
| 1 | Nd0.25Li0.25TaO3, Liverpool 1.91e-6 vs OBELiX 1.31e-8 S/cm, resid +2.16, *unexplained; nearest S/m stored as S/cm (×100), off by 0.16* | Source: Mizumoto & Hayashi, *Solid State Ionics* 116 (1999) 263, 10.1016/S0167-2738(98)00414-7. **Not in Bond's corpus**; read from the PDF. The paper reports σ in **S m⁻¹** and plots σT in S m⁻¹ K; room-temperature Nd is ≈1e-8 S cm⁻¹ from its Figs. 3–4. | **Liverpool error, ×100 (S/m stored as S/cm).** Matches the case Wang et al. (arXiv 2609.01621) found by hand. |
| 2 | Li6.5La3Zr1.75Te0.25O12 and Li6.75La3Zr1.875Te0.125O12, Liverpool ≈10× below OBELiX, *S/m vs mS/cm (×10)* | Source: Deviannapoorani et al., *J. Power Sources* 240 (2013) 18, 10.1016/j.jpowsour.2013.03.166, read from the PDF. Table 2 (30 °C): 1.02e-3 and 3.30e-4 S cm⁻¹, which equal OBELiX. Liverpool stores 1.07e-4 and 3.77e-5 at the same 30 °C. | **Liverpool error**: 9.5× and 8.7× below the table. The "×10" label fits the size, but the digits differ (1.07 vs 1.02, 3.77 vs 3.30), so the mechanism is *unconfirmed*. |
| 3 | AlCoCrFeNiTi0.5, MPEA YS 2260 MPa with HV 178, *unexplained* (hardness vs yield strength) | Source: Zhou et al., *APL* 90, 181904 (2007), 10.1063/1.2734517, read from the PDF. Reports YS 2.26 GPa (compression); **reports no hardness**. | **MPEA error: HV not supported by the cited source.** The paper's Table I gives Young's modulus E = 177.7 GPa for Ti0.5, and MPEA stores 178 as both HV and E in this row, so the HV is most likely the modulus in the wrong column. |
| 4 | Li3PS4, Liverpool 1.6e-4 vs OBELiX 2.6e-7 / 8.9e-7 S/cm, resid +2.3 to +2.8, *unexplained* | **Bond:** Liu et al., *JACS* 2013, 10.1021/ja3110895 (880 citations): nanoporous **β**-Li3PS4 raises room-temperature σ **by 3 orders of magnitude** over bulk. Bond also found Yang et al., *ACS AMI* 2016 (10.1021/acsami.6b06754), confirming 1.64e-4 S cm⁻¹ for nanoporous β. | **Not an error: nanoporous β vs bulk samples from the same paper** (OBELiX joc is γ, SG 31; nhq is β, SG 62), stored under one composition. A real limitation: matching by composition alone can't tell polymorphs apart. |
| 5 | Sm0.52Li0.38TiO2.97, Liverpool 1.5e-3 vs OBELiX 2.0e-7, resid +3.9, *unexplained* | Source 10.1016/0167-2738(94)90310-7 (*Solid State Ionics* 1994). **Not in Bond's corpus**; paper not yet read. A 7,500× gap fits no single factor; ×1000 plus a temperature/phase mismatch is possible. | **Open.** Needs the paper. |

**ChemRxiv re-check (2026-10-21):** Bond added ChemRxiv (57k preprints, 2017 onwards). Re-searching the open
flags (Sm-Li titanate, Li4B7O12Cl) found only unrelated recent electrolyte preprints; their sources (1977, 1994)
predate ChemRxiv, so case 5 stays open.

**Bond coverage note:** Bond (PubMed + arXiv + bioRxiv/medRxiv + others) found the *JACS* and *ACS*
sources instantly but not older *Solid State Ionics* papers (cases 1 and 5). Tracing those needs
publisher access.

## Agent traces (`trace_flags.workflow.js`, 2026-10-22)
One tracer agent per flag (Valency Bond + OpenAlex abstracts, verbatim quotes required) and one independent skeptic
that re-fetches the source, checks the quote verbatim and tries to refute the verdict. **Confirmed** = quote verified,
not refuted, verdict not "unclear". Full records: `traces_agent.json`. Ids are stable (`check/entry[/partner]`, as written by `audit.py` to `flags.json`); `traces_agent.json` also keeps the old rank labels (`old_id`).

**Calibration on the 6 hand-traced flags** (`cross_db/liverpool:792:ionic_conductivity/obelix:joc`, `cross_db/liverpool:792:ionic_conductivity/obelix:nhq`, `cross_db/liverpool:615:ionic_conductivity/obelix:il5`, `cross_db/liverpool:23:ionic_conductivity/obelix:uht`, `cross_db/liverpool:771:ionic_conductivity/obelix:r07`, `relation_tabor/mpea:113:YS/mpea:113`; plus `cross_db/liverpool:617:ionic_conductivity/obelix:o23` from the same paper as
`cross_db/liverpool:615:ionic_conductivity/obelix:il5`): the agents never contradicted a hand verdict and confirmed nothing false, but they stay "unclear" when no open
text states the number: closed papers without an abstract (the 1999 tantalate, Te-LLZO) and abstracts without
absolute values (Li₃PS₄). Only 24 of the 75 flagged papers have an open abstract (`prescreen.py`); 11 flags (of 116 at the
time) came from abstracts that state a value with a matching unit, so the agents were run on those plus the
calibration set (17 flags). After the review fixes the audit has 119 flags and the pre-screen finds 10: one traced
series was split by material family and is no longer flagged. Bond held few of these sources; the confirmed verdicts rest on OpenAlex abstracts.

| Flag | Check | Composition | Agent verdict | Skeptic | Evidence |
|---|---|---|---|---|---|
| `cross_db/liverpool:584:ionic_conductivity/obelix:xnb` | cross_db | Li5PS4(BH4)2 | **database error** | **confirmed** | abstract: "1.8 × 10–3 S cm–1 at 25 °C" for the x = 50 sample; OBELiX 1.8e-3 matches, Liverpool 7.96e-3 (4.4×) does not |
| `cross_paper/obelix:etz:ionic_conductivity` | cross_paper | Li7La3Zr2O12 (OBELiX) | **physical difference** | **confirmed** | abstract: Al-free tetragonal LLZO "about two orders of magnitude lower (2 × 10(-6) Scm(-1)…)"; reference papers are cubic |
| `cross_db/liverpool:19:ionic_conductivity/obelix:kji` | cross_db | Li6.4La3Zr1.4Ta0.6O12 | **physical difference** (likely) | **confirmed** | abstract: "σLi ≈ 1.0 × 10−3 S cm−1 for x = 0.6" at RT (= OBELiX); Liverpool's row is at 34 °C. The temperature explains ~1.5× of the 2×; Liverpool's own value is not in the abstract, so counted as likely, not settled |
| `cross_db/liverpool:727:ionic_conductivity/obelix:883` | cross_db | LiAlH4 | database error | unclear | abstract: "8.7×10−9 S/cm in the case of LiAlH4" (= OBELiX); Liverpool 2.0e-9 not in the abstract, but the full text may hold it |
| `arrhenius/liverpool:665:ionic_conductivity` | arrhenius | Li3O(Cl0.5Br0.5) | unclear (leans physical) | unclear | abstract: σ rises "> 10(-2) S/cm and beyond" near melting: the tool's "×10" is likely a superionic jump |
| `relation_tabor/mpea:1522:YS/mpea:1522` | relation_tabor | AlCrFeNiMo0.5Ti0.75 | unclear | unclear | abstract confirms HV 766.2; gives no yield strength for x = 0.75 |
| `cross_paper/obelix:p9u:ionic_conductivity`, `arrhenius/liverpool:586:ionic_conductivity (no longer flagged)`, `arrhenius/liverpool:664:ionic_conductivity`, `cross_paper/mpea:1267:YS` | various | — | unclear | unclear | abstract states no number for that sample |
| `cross_db/liverpool:792:ionic_conductivity/obelix:joc`, `cross_db/liverpool:792:ionic_conductivity/obelix:nhq`, `cross_db/liverpool:615:ionic_conductivity/obelix:il5`, `cross_db/liverpool:23:ionic_conductivity/obelix:uht`, `cross_db/liverpool:771:ionic_conductivity/obelix:r07`, `relation_tabor/mpea:113:YS/mpea:113` | calibration | — | unclear | unclear | no number in any open text (hand verdicts above stand) |
| `cross_db/liverpool:617:ionic_conductivity/obelix:o23` | cross_db | Li0.25La0.25TaO3 | unclear | unclear | closed 1999 paper; the gap (14×) differs from the Nd pair's (146×) in the same paper, so not one unit slip |

**Tally (18 flags traced):** settled 8 (database error 5: `cross_db/liverpool:615:ionic_conductivity/obelix:il5`, `cross_db/liverpool:23:ionic_conductivity/obelix:uht`, `cross_db/liverpool:771:ionic_conductivity/obelix:r07`, `relation_tabor/mpea:113:YS/mpea:113`, `cross_db/liverpool:584:ionic_conductivity/obelix:xnb`; physical 3: `cross_db/liverpool:792:ionic_conductivity/obelix:joc`, `cross_db/liverpool:792:ionic_conductivity/obelix:nhq`,
`cross_paper/obelix:etz:ionic_conductivity`), likely physical 1 (`cross_db/liverpool:19:ionic_conductivity/obelix:kji`), open 9 (`cross_db/liverpool:605:ionic_conductivity/obelix:i6k`, `cross_paper/obelix:p9u:ionic_conductivity`, `cross_db/liverpool:617:ionic_conductivity/obelix:o23`, `arrhenius/liverpool:665:ionic_conductivity`, `cross_db/liverpool:727:ionic_conductivity/obelix:883`, `relation_tabor/mpea:1522:YS/mpea:1522`, `arrhenius/liverpool:586:ionic_conductivity (no longer flagged)`, `arrhenius/liverpool:664:ionic_conductivity`, `cross_paper/mpea:1267:YS`). `cross_db/liverpool:730:ionic_conductivity/obelix:6l9` (Li4B7O12Cl) was
only searched for (ChemRxiv re-check above), not traced.
