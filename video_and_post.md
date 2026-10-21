# Video script (≤ 4 min, normal speed) and social post

## Video: screen recording + voice

**0:00–0:35 · Problem** (show Wang et al. abstract, then the Liverpool CSV)
> "Every ML model for materials is trained on numbers copied out of papers. Those numbers carry hidden
> errors: a value in siemens per metre stored as siemens per centimetre is a hundred times off, but still
> looks perfectly plausible, so no outlier filter catches it. This summer a group traced one such error
> into a public database by hand. I built a tool that finds them automatically."

**0:35–1:10 · Idea** (show figure panel A and the audit.py FACTORS dict)
> "LitAudit checks every value against independent references: the same paper's value in a second
> database, and physics relations the value must satisfy. When they disagree, it asks: is the gap a known
> unit or quantity factor? Times 10, 100, 1000, sigma-T vs sigma, ksi vs MPa. If yes, it names the cause.
> If not, it says 'unexplained' and shows the nearest factor. It never silently relabels."

**1:10–2:40 · Live run** (terminal: `python audit.py`, then the notebook)
> "Two public conductivity databases share 128 entries; 110 agree. Here's the top of the flag list.
> [point] This tantalate is 145 times apart. I opened the 1998 paper: it reports in siemens per metre, and
> one database stored that as per centimetre. That's exactly the error found by hand, found automatically.
> [point] These two garnets: the paper's own table matches OBELiX, so Liverpool is about 8 times too low.
> [panel B] Same code, different domain: alloy hardness vs yield strength. This alloy claims 2.26 GPa
> strength with the hardness of mild steel. I read the paper: it never reports a hardness. Provenance error.
> [traces.md] For the next flag, Li3PS4, I used Valency Bond: it found the source paper in seconds. The
> 1000-times gap is real physics: nanoporous beta phase vs bulk gamma phase. Not an error, and the tool
> correctly didn't call it one."

**2:40–3:30 · Evidence + limits** (panel C)
> "To measure it, I planted each error type into clean comparisons: conductivity and density unit errors
> are named correctly 94 to 100 percent of the time; hardness errors are always flagged but named only
> half the time, because that relation is noisy. Limits: composition can't separate polymorphs, and only
> one published case lives in an open database, so most of the numbers come from planted errors."

**3:30–3:55 · Impact**
> "Literature databases are infrastructure for AI-driven discovery. LitAudit tells curators which entries
> disagree, why, and where to look, and adding a new property is just its units and relations. Code is open; link below."

## Social post (LinkedIn / X thread)

> 🔍 **LitAudit: finding hidden errors in the databases AI for materials is trained on**, built solo at
> #OSIHackathon2026 (Bochum hub).
>
> Literature-derived materials databases contain *structured* errors: S/m stored as S/cm (×100), σT
> stored as σ (×298), MPa vs GPa. They look plausible, so filters miss them.
>
> LitAudit checks every value against a second database and physics relations, then names the unit
> mix-up behind each disagreement, or says "unexplained".
>
> On public Li-ion conductivity and high-entropy-alloy databases it flagged entries that I confirmed
> against the original papers: a ×100 unit error (the case found by hand in a 2026 study), a ≈8× error,
> and a hardness value the cited paper never reports. Planted unit errors are recovered 94–100% of the time.
>
> Literature traced with @Valency MCP Bond. 🎥 video below · 💻 code: https://github.com/shivasish-mishra/litaudit
>
> #AIforScience #MaterialsInformatics #LLMHackathon
