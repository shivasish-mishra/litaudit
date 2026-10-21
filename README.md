# LitAudit

Audits literature-derived materials databases for structured errors (unit and quantity mix-ups,
values missing from their cited source). It checks each value against independent sources
(another database, a physics relation, other reports of the same material) and diagnoses
disagreements.

OSI Hackathon 2026 project (Bochum hub).

## Setup
```bash
pip install -r requirements.txt
python fetch_data.py      # downloads the source databases into data/ (not committed)
python test_loaders.py && python test_audit.py
python audit.py           # run all checks, print flags + planted-error benchmark
python figures.py         # figures/litaudit.png
```
Interactive version: `jupyter lab audit.ipynb`.

## How it works
- `loaders.py`: all databases into one long table (one row per value, normalised composition).
- `audit.py`: checks (`cross_db`, `relations`), the per-property factor library `FACTORS`,
  `diagnose` (agree / named factor / unexplained + nearest factor), `planted_benchmark`.
- `traces.md`: top flags traced to their source papers (Valency MCP Bond + PDFs).
- `writeup.md`: one-page summary of method and results.

To add a property: load it into the long table, add its known unit factors to `FACTORS`,
and (optionally) a relation in `relations()`.

## Data
| Database | Property | Licence |
|---|---|---|
| Liverpool Li-ion conductivity (Hargreaves et al., *npj Comput. Mater.* 2023) | σ(T) | Academic use; cite the University of Liverpool. Not redistributed here. |
| OBELiX (NRC/Mila) | room-temperature σ | CC-BY 4.0 |
| MPEA (Borg et al., *Sci. Data* 2020) | HV, YS, UTS, E, density | Apache 2.0 |
