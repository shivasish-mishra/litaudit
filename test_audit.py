"""Run: python test_audit.py  (data checks need fetch_data.py first)."""
import itertools
import math

import numpy as np
import pandas as pd

from audit import T_SLIP, arrhenius, cross_paper, diagnose, entry_verdicts, nearest, noise, run
from loaders import DATA


def table(rows):
    base = {"db": "syn", "doi": "p", "composition": "Li", "comp_key": "Li1", "property": "ionic_conductivity",
            "unit": "S/cm", "T_assumed": False, "condition": ""}
    return pd.DataFrame([{**base, "row_id": str(i), **r} for i, r in enumerate(rows)])


# --- Arrhenius check: a planted slip is pinned on the right point, at every position, and named ---
T = np.array([300, 350, 400, 450, 500, 550.0])
sigma = 1e-2 * np.exp(-0.5 / (8.617e-5 * T)) / T
for bad in range(len(T)):
    for mult, name in ((10, "S/m vs mS/cm (x10)"), (100, "S/m stored as S/cm (x100)"),
                       (1000, "mS/cm stored as S/cm (x1000)")):
        v = sigma.copy()
        v[bad] *= mult
        r = arrhenius(table([{"value": a, "T_K": b} for a, b in zip(v, T)]))
        flagged = r[r.diagnosis != "agree"]
        assert list(zip(flagged.key_a, flagged.diagnosis)) == [(f"syn:{bad}:ionic_conductivity", name)], (bad, mult)
clean = arrhenius(table([{"value": a, "T_K": b} for a, b in zip(sigma, T)]))
assert (clean.diagnosis == "agree").all() and clean.attributable.all()
# a temperature stored in K under a degC label (T_K too high by 273.15) is named
T2 = T.copy()
T2[2] += 273.15
r = arrhenius(table([{"value": a, "T_K": b} for a, b in zip(sigma, T2)]))
assert r[r.diagnosis != "agree"].diagnosis.tolist() == [T_SLIP]
# 3-temperature series: only the middle point is judged, and not attributably (could be either end)
r = arrhenius(table([{"value": a, "T_K": b} for a, b in zip(sigma[:3] * [1, 100, 1], T[:3])]))
assert len(r) == 1 and not r.attributable.iloc[0]

# --- cross-paper check: with >= 3 papers the odd one out is attributable, with 2 it is not ---
rows = [{"doi": d, "value": v, "T_K": 298.15} for d, v in (("a", 1e-4), ("b", 1.2e-4), ("c", 0.9e-4), ("d", 1e-1))]
cp = cross_paper(table(rows))
odd = cp[cp.doi == "d"]
assert odd.attributable.all() and (odd.diagnosis != "agree").all()
assert not cross_paper(table(rows[:1] + rows[3:])).attributable.any()

# --- naming needs resolution: a check whose scatter is ~0.6 dex flags but never names a cause ---
assert noise(pd.Series(np.random.default_rng(0).normal(0, 0.6, 500)))[1] == 0.0
assert diagnose(2.0, "ionic_conductivity", tol=0.0, agree=1.8) == "unexplained"

# --- entry verdicts: a symmetric disagreement is pinned only on the side whose partner alone is confirmed ---
pair = {"check": "cross_db", "key_a": "A", "key_b": "B", "attributable": False,
        "diagnosis": "S/m stored as S/cm (x100)", "resid": 2.0, "agree": 0.3}
ok = {"check": "cross_paper", "key_b": "", "attributable": True, "diagnosis": "agree", "resid": 0.1, "agree": 0.3}


def verdicts(*rows):
    return entry_verdicts(pd.DataFrame(rows)).set_index("key").verdict.to_dict()


assert verdicts(pair, {**ok, "key_a": "B"}) == {"A": "suspect", "B": "clean"}
assert verdicts(pair, {**ok, "key_a": "B"}, {**ok, "key_a": "A"}) == {"A": "ambiguous", "B": "ambiguous"}
assert verdicts(pair, {**ok, "key_a": "B", "agree": 2.5})["A"] == "ambiguous"     # band wider than the gap
assert verdicts(pair, {**ok, "key_a": "B", "check": "arrhenius"})["A"] == "ambiguous"  # own series: no scale check

# --- Arrhenius: two slips in one series are both pinned, and only they (no good neighbour blamed) ---
T8 = np.linspace(300, 650, 8)
s8 = 1e-2 * np.exp(-0.5 / (8.617e-5 * T8)) / T8
for i, j in itertools.combinations(range(8), 2):
    v = s8.copy()
    v[[i, j]] *= 100
    r = arrhenius(table([{"value": a, "T_K": b} for a, b in zip(v, T8)]))
    flagged = sorted(r[r.diagnosis != "agree"].key_a.str.split(":").str[1].astype(int))
    assert flagged == [i, j], (i, j, flagged)
# a culprit beyond the testable range is reported (unnamed, not attributable), not silently dropped
Tf = np.array([298, 373, 398, 423, 448.0])
v = 1e-2 * np.exp(-0.5 / (8.617e-5 * Tf)) / Tf
v[0] *= 100
r = arrhenius(table([{"value": a, "T_K": b} for a, b in zip(v, Tf)]))
far = r[r.key_a == "syn:0:ionic_conductivity"]
assert len(far) == 1 and far.diagnosis.iloc[0] == "unexplained" and not far.attributable.iloc[0], r

c = "ionic_conductivity"
assert diagnose(0.1, c) == "agree"
assert diagnose(2.03, c) == "S/m stored as S/cm (x100)"
assert diagnose(-2.97, c) == "mS/cm stored as S/cm (x1000)"
assert diagnose(math.log10(298), c) == "sigma*T stored as sigma (~x298)"
assert diagnose(1.6, c) == "unexplained"
assert nearest(2.16, c).startswith("S/m stored as S/cm (x100), off by 0.16")
assert diagnose(3.0, "density_exp") == "measured kg/m3 stored as g/cm3 (x1000)"
assert diagnose(-3.0, "density_exp") == "unexplained"  # directed: a kg/m3 slip can only raise the measured value
# HV-in-MPa (-0.99) and YS-in-ksi (-0.84) are closer than the relation's noise; the stored HV breaks the tie
assert diagnose(-0.9, "HV_vs_YS", 0.25, ref=300) == "YS: ksi stored as MPa (x6.9)"
assert diagnose(-0.9, "HV_vs_YS", 0.25, ref=3000) == "HV given in MPa (x9.8)"
# verified provenance case (YS too HIGH for its HV) must not be blamed on a unit that only lowers YS
assert diagnose(+0.65, "HV_vs_YS", 0.25, ref=178) == "unexplained"

if (DATA / "liverpool.csv").exists():
    checks = run(__import__("loaders").load_all())
    # verified against the papers (see traces.md): all three must be flagged
    for doi in ("10.1016/s0167-2738(98)00414-7", "10.1016/j.jpowsour.2013.03.166", "10.1063/1.2734517"):
        assert (checks[checks.doi == doi].diagnosis != "agree").any(), doi
    nd = checks[(checks.doi == "10.1016/s0167-2738(98)00414-7") & (checks.composition == "Nd0.25Li0.25TaO3")]
    assert "x100" in nd.nearest.iloc[0], nd
    print(f"ok ({len(checks)} comparisons)")
else:
    print("ok (unit checks only)")
