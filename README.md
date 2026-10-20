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
python test_loaders.py
python loaders.py         # summary of the long table
```

## Data
| Database | Property | Licence |
|---|---|---|
| Liverpool Li-ion conductivity (Hargreaves et al., *npj Comput. Mater.* 2023) | σ(T) | Academic use; cite the University of Liverpool. Not redistributed here. |
| OBELiX (NRC/Mila) | room-temperature σ | CC-BY 4.0 |
| MPEA (Borg et al., *Sci. Data* 2020) | HV, YS, UTS, E, density | Apache 2.0 |
