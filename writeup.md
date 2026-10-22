# LitAudit: catching hidden errors in the databases AI for materials learns from

**Shivasish Mishra** · OSI Hackathon 2026 (Bochum hub) · code: https://github.com/shivasish-mishra/litaudit · video: https://lnkd.in/p/edVfuGZh

**Problem.** Many materials ML models are trained on databases of values copied out of papers. Unit and quantity
slips (S/m stored as S/cm, σT stored as σ, MPa vs GPa) shift a value by a fixed factor yet leave it plausible, so
outlier filters miss them. Wang et al. (arXiv 2609.01621, 2026) traced one such 100× error into a public Li-ion
conductivity database by hand.

**What LitAudit does.** It compares each value with references it should agree with: (1) the same paper in a second
database, (2) the paper's own temperature series, (3) other papers on the same material, (4) physics relations
(hardness vs yield strength, measured vs calculated density). A gap close to a known factor (×10, ×100, ×1000, ×298
for σT, K vs °C…) is named; any other gap is "unexplained". Thresholds come from each check's own scatter. (5) A
Claude Code agent workflow traces flags to their sources through Valency MCP Bond and OpenAlex, and a second agent
re-fetches each source and tries to refute the verdict. Tested on Li-ion conductivity (Liverpool, OBELiX) and
high-entropy alloys (MPEA): 5,357 values.

![LitAudit figure](figures/litaudit.png)
*A: 203 matched pairs between the two conductivity databases (dashed: ×10, ×100, ×1000). B: hardness vs yield
strength. C: planted slips, whole audit re-run. D: the Arrhenius check on a real series with a planted ×100 slip.*

**Results.** 1,663 comparisons, 119 flags. 37% of stored values have at least one reference (51% of conductivity
values). Where a value has one, planted slips are flagged 76–100% of the time, the right cause is named for 71–94%,
and 0.3–1.1% of clean values are falsely flagged.

**Checked against the sources.** 18 flags were traced (7 by hand, 11 by the agents) and 8 could be settled. Five were
database errors: a Nd tantalate stored in S/m as S/cm (the case Wang et al. found by hand); two Te-doped garnets 9.5×
and 8.7× below the paper's table; an alloy whose "hardness" of 178 HV matches the paper's Young's modulus (177.7 GPa),
while the paper reports no hardness; and Li₅PS₄(BH₄)₂, stored as 7.96×10⁻³ S/cm against the abstract's "1.8 × 10⁻³
S cm⁻¹ at 25 °C" (found by the agents). Three were real physics: the same formula in different structures (tetragonal
vs cubic LLZO; nanoporous vs bulk Li₃PS₄). A flag therefore means "check this", not "this is wrong". Nine stay open,
mostly because no open text states the value (51 of the 75 flagged papers have no abstract in OpenAlex).

**Limits.** Composition alone cannot separate polymorphs or processing; with only two values a disagreement cannot say
which side is wrong; where a cause was named on real data, no source has confirmed it yet; 63% of values still have no
reference.

**Builds on.** Data: Liverpool Ionics Dataset (Hargreaves et al., npj Comput. Mater. 2023; academic use, not
redistributed), OBELiX (NRC/Mila, CC-BY 4.0), MPEA (Borg et al., Sci. Data 2020, Apache 2.0). Tools: OpenAlex API,
Valency MCP Bond, Claude Code (agent workflow and coding assistant), pandas, NumPy, matplotlib. The audit code is new,
written for this hackathon. Details: `README.md`, `traces.md`.
