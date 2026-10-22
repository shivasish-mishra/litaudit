# Video and social post

## Video
Built by `../video/make_video.py` (slides + real terminal demo + narration, ≤ 4 min, normal speed); the narration
text is written to `../video/narration.txt`. Record your own voice per slide into `../video/myvoice/slideNN.*`
to replace the synthetic one.

## Social post (LinkedIn / X)

> 🔍 **LitAudit: finding hidden errors in the databases AI for materials is trained on**, built solo at
> #OSIHackathon2026 (Bochum hub).
>
> Literature-derived materials databases contain *structured* errors: S/m stored as S/cm (×100), σT stored as σ,
> MPa vs GPa, a temperature in K under a °C label. They look plausible, so filters miss them.
>
> LitAudit compares values with independent references (a second database, their own temperature series, other
> papers, physics relations) and names the slip behind a disagreement, or says "unexplained". Agents (with
> @Valency MCP Bond and OpenAlex) then trace flags to their sources, and a skeptic agent tries to refute them.
>
> Of 8 real flags settled against the sources, 5 were database errors (including a ×100 slip found by hand in a
> 2026 study, and a new one the agents found) and 3 were genuine physics (polymorphs). Planted slips are flagged
> 76–100% of the time with about 1% false alarms. Limits stated honestly in the write-up.
>
> 🎥 video below · 💻 code: https://github.com/shivasish-mishra/litaudit
>
> #AIforScience #MaterialsInformatics #LLMHackathon
