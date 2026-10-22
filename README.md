# LitAudit

Audits literature-derived materials databases for structured errors: unit and quantity mix-ups that
shift a value by a fixed factor (S/m stored as S/cm, σT stored as σ, MPa vs GPa, a temperature in K
under a °C label). Tracing flags to their sources can also expose values that are not in the cited paper. Each value is compared with independent
references; disagreements are diagnosed as a named cause, or reported as unexplained with the nearest
cause shown. Flags can then be traced to their source papers by an agent workflow.

OSI Hackathon 2026 project (Bochum hub). One-page write-up: [writeup.md](writeup.md); source traces: [traces.md](traces.md).
Video (3.5 min, LinkedIn): https://lnkd.in/p/edVfuGZh

## Setup
```bash
pip install -r requirements.txt
python fetch_data.py      # downloads the source databases into data/ (not committed)
python test_loaders.py && python test_audit.py
python audit.py 30        # all checks, top 30 flags, entry verdicts, coverage, end-to-end benchmark (~1.5 min)
python figures.py         # figures/litaudit.png, panel_a..d.png, benchmark.csv
```
Interactive version: `jupyter lab audit.ipynb`.

## How it works
Four automatic checks (`audit.py`), each producing comparisons `log10(value / reference)`:

| Check | Reference | Who is to blame |
|---|---|---|
| `cross_db` | the same paper + composition in a second database | symmetric (either side) |
| `arrhenius` | the same paper's temperature series: each point vs its neighbours in log σT vs 1/T (interpolation; end points by a local line, capped at 2 neighbour spacings) | the point, via a removal test (series of ≥ 4 temperatures) |
| `cross_paper` | each entry vs the median of other papers' medians for the same composition and condition (OBELiX: space group; MPEA: processing, plus test type for strength) in one database | the entry, when ≥ 3 papers report it |
| `relations` | physics: hardness vs yield strength (Tabor, calibrated on the data), measured vs calculated density | symmetric |

- **Noise sets every threshold.** From each check's robust scatter σ: agreement band `max(0.3, 3σ)` dex,
  factor tolerance `2σ` (0.10–0.25 dex). A check too noisy to resolve the factor ladder (σ > 0.2 dex, e.g.
  papers vs papers for conductivity, σ ≈ 0.6) still flags outliers but never names a cause.
- **Diagnosis** (`FACTORS`, `DIRECTED`): the gap is matched to known factors; in physics relations factors are
  signed (a ksi slip can only lower a yield strength); a physical range breaks ties (HV > 1500 is not a Vickers
  number); a temperature slip is tested by re-reading T as kelvin.
- **Entry verdicts** (`entry_verdicts`): all checks combined per database entry → *suspect*, *ambiguous*, *clean*.
  A symmetric disagreement is pinned on one side only if the other side alone is confirmed: it passes an
  attributable check against other sources whose band is narrower than the gap (its own series cannot confirm scale).
- **Benchmark** (`planted_benchmark`): corrupt stored values with each of the 9 factors in `PLANT` (the temperature slip and UTS factors are not
  benchmarked), re-run the whole audit, measure
  flagged / named / pinned and the collateral false-flag rate.

## Literature tracing (agents)
`python audit.py` writes `flags.json` (every flag, with stable ids such as
`cross_db/liverpool:615:ionic_conductivity/obelix:il5`). `python prescreen.py` fetches OpenAlex abstracts and
writes `data/trace_todo.json`: the flags whose source abstract states a value in a matching unit (10 of 119 today;
24 of the 75 flagged papers have an open abstract). `trace_flags.workflow.js` is a Claude Code workflow: one agent
per flag finds the source through **Valency MCP Bond** (PubMed, arXiv, ChemRxiv…) and the OpenAlex API, quotes what
the source reports and judges *database error / physical difference / unclear*; an independent skeptic re-retrieves
the source, checks the quote verbatim and tries to refute the verdict. Run it from Claude Code with the Workflow tool,
`args: {ids: [...]}` (the ids from `trace_todo.json`); it reads `flags.json` from `args.flags` (default: the path in `FLAGS`).
The Bond tool names in `TOOLS` carry this author's connector id (`34b41fbe-…`); replace it with your own. Results: `traces.md`, `traces_agent.json`.

## Which properties can be audited? (scope and limits)
Any **scalar, numeric property with units** works, if it has **at least one independent reference**:

| Needs | Why | If missing |
|---|---|---|
| Known unit / quantity confusions | the factor library is what names a cause | add them to `FACTORS` (one line); without any, LitAudit can still flag but not name |
| A second report or a law it must obey | nothing to compare a single value with | only plausibility ranges are possible (not yet implemented) |
| The conditions that change it (T, phase, test type, processing) | otherwise real differences look like errors (tetragonal vs cubic LLZO ≈ ×100) | put them in `condition` (used by `arrhenius` and `cross_paper`; `cross_db` matches paper + composition only) |
| Log-scale behaviour | gaps are judged as ratios | for signed or near-zero quantities (Seebeck coefficient, formation energy) use differences instead of ratios — not yet implemented |

Not suited as is: categorical properties (crystal structure, phase labels), tensors without orientation metadata,
and properties reported only once. Adding a property = load it into the long table (`loaders.py`), add its unit
factors, and optionally a relation (`relations()`) or a series law (like `arrhenius()`, e.g. Hall–Petch for
yield strength vs grain size, Vegard for lattice parameter vs composition).

## Example: a literature query
`python examples/h_in_al.py` audits reported hydrogen diffusivities in Al (lattice vs trapped-effective vs grain
boundary) taken from paper abstracts, with a `diffusivity` unit spec. It compares sources only inside their
fitted temperature ranges: at 298 K a DFT and an experimental lattice law differ by exactly 2.0 dex, which naive
factor matching would mislabel as a cm²/s vs mm²/s slip, but it is Arrhenius extrapolation.

## Data
| Database | Property | Licence |
|---|---|---|
| Liverpool Li-ion conductivity (Hargreaves et al., *npj Comput. Mater.* 2023) | σ(T) | Academic use; cite the University of Liverpool. Not redistributed here (`traces.md` / `traces_agent.json` quote a few flagged values). |
| OBELiX (NRC/Mila) | room-temperature σ, space group | CC-BY 4.0 |
| MPEA (Borg et al., *Sci. Data* 2020) | HV, YS, UTS, E, density | Apache 2.0 |

This project builds on these datasets; all audit code is new.
