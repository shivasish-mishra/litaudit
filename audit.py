"""Compare each value with independent references and diagnose any disagreement.

A check produces rows: check, db, doi, composition, property, value, reference, resid, diagnosis, nearest, detail
- resid = log10(value / reference)
- diagnosis = 'agree' | <named unit/quantity factor> | 'unexplained'
- nearest = for 'unexplained', the closest known factor and its distance (no auto-relabelling)
"""
import math

import numpy as np
import pandas as pd

AGREE = 0.3  # |resid| below this = consistent (lab-to-lab scatter is ~0.3 dex for conductivity)
TOL = 0.1    # how close |resid| must be to a known factor to name it

L = math.log10
# Known unit/quantity confusions per property, as log10 of the factor they introduce.
FACTORS = {
    "ionic_conductivity": {"S/m stored as S/cm (x100)": 2, "mS/cm stored as S/cm (x1000)": 3,
                           "S/m vs mS/cm (x10)": 1, "sigma*T stored as sigma (~x298)": L(298)},
    "YS": {"GPa vs MPa (x1000)": 3, "ksi vs MPa (x6.9)": L(6.895)},
    "UTS": {"GPa vs MPa (x1000)": 3, "ksi vs MPa (x6.9)": L(6.895)},
    "HV": {"HV given in GPa (x102)": L(1 / 0.009807), "HV given in MPa (x9.8)": L(9.807)},
    "density_exp": {"kg/m3 vs g/cm3 (x1000)": 3},
}
FACTORS["HV_vs_YS"] = {**FACTORS["HV"], **FACTORS["YS"]}  # either side could be wrong


def diagnose(resid, prop):
    r = abs(resid)
    if r < AGREE:
        return "agree"
    for name, f in FACTORS.get(prop, {}).items():
        if abs(r - f) < TOL:
            return name
    return "unexplained"


def nearest(resid, prop):
    """Closest known factor and how far off it is (shown for 'unexplained' so a human can judge)."""
    f = FACTORS.get(prop, {})
    if not f:
        return ""
    name = min(f, key=lambda k: abs(abs(resid) - f[k]))
    return f"{name}, off by {abs(abs(resid) - f[name]):.2f}"


def _finish(out, check):
    out["check"] = check
    out["diagnosis"] = [diagnose(r, p) for r, p in zip(out.resid, out.property)]
    out["nearest"] = [nearest(r, p) if d == "unexplained" else ""
                      for r, p, d in zip(out.resid, out.property, out.diagnosis)]
    return out[["check", "db", "doi", "composition", "property", "value",
                "reference", "resid", "diagnosis", "nearest", "detail"]].reset_index(drop=True)


def cross_db(df, max_dT=10):
    """Same paper + same composition + same property in two databases, at about the same T."""
    m = df.merge(df, on=["doi", "comp_key", "property"])
    m = m[(m.db_x < m.db_y) & ((m.T_K_x - m.T_K_y).abs() <= max_dT)]
    out = pd.DataFrame({
        "db": m.db_x + " vs " + m.db_y, "doi": m.doi, "composition": m.composition_x,
        "property": m.property, "value": m.value_x, "reference": m.value_y,
        "resid": np.log10(m.value_x / m.value_y),
        "detail": m.row_id_x + " / " + m.row_id_y,
    })
    return _finish(out, "cross_db")


def relations(df):
    """Physics relations between properties of the same database row (MPEA)."""
    rows = df[df.db == "mpea"].pivot_table(index=["row_id", "doi", "composition", "condition", "T_K"],
                                           columns="property", values="value").reset_index()
    rt = rows[(rows.T_K - 298.15).abs() <= 10]
    parts = []

    # Tabor: YS ~ HV*g/3. The constant varies by alloy class, so calibrate on the data (median per test type).
    t = rt.dropna(subset=["HV", "YS"]).copy()
    t["test"] = t.condition.str.split("|").str[0]
    t["ratio"] = np.log10(t.YS / (t.HV * 9.807 / 3))
    t["resid"] = t.ratio - t.groupby("test").ratio.transform("median")
    parts.append(_finish(pd.DataFrame({
        "db": "mpea", "doi": t.doi, "composition": t.composition, "property": "HV_vs_YS",
        "value": t.YS, "reference": t.HV, "resid": t.resid,
        "detail": "YS (MPa) vs HV, test " + t.test,
    }), "relation_tabor"))

    # Measured vs calculated (rule-of-mixtures) density; porosity only lowers the measured value.
    d = rows.dropna(subset=["density_exp", "density_calc"])
    parts.append(_finish(pd.DataFrame({
        "db": "mpea", "doi": d.doi, "composition": d.composition, "property": "density_exp",
        "value": d.density_exp, "reference": d.density_calc,
        "resid": np.log10(d.density_exp / d.density_calc), "detail": "measured vs calculated",
    }), "relation_density"))
    return pd.concat(parts, ignore_index=True)


def planted_benchmark(checks, frac=0.3, seed=0):
    """Plant each known factor into agreeing comparisons and measure how often it is named.

    Equivalent to corrupting the stored value, since resid = log10(value/reference).
    Returns one row per (property, factor): n planted, recall (named exactly), flagged (any non-agree).
    """
    rng = np.random.default_rng(seed)
    clean = checks[checks.diagnosis == "agree"]
    rows = []
    for prop, factors in FACTORS.items():
        base = clean[clean.property == prop]
        if base.empty:
            continue
        for name, f in factors.items():
            s = base.sample(frac=frac, random_state=int(rng.integers(1e9))) if len(base) > 10 else base
            sign = rng.choice([-1, 1], size=len(s))
            got = [diagnose(r + g * f, prop) for r, g in zip(s.resid, sign)]
            rows.append({"property": prop, "factor": name, "n": len(s),
                         "recall": np.mean([x == name for x in got]),
                         "flagged": np.mean([x != "agree" for x in got])})
    return pd.DataFrame(rows)


def run(df):
    return pd.concat([cross_db(df), relations(df)], ignore_index=True)


if __name__ == "__main__":
    from loaders import load_all
    checks = run(load_all())
    print(checks.groupby(["check", "diagnosis"]).size().to_string(), "\n")
    flags = checks[checks.diagnosis != "agree"].sort_values("resid", key=abs, ascending=False)
    with pd.option_context("display.width", 200, "display.max_colwidth", 40):
        print(flags[["check", "composition", "value", "reference", "resid", "diagnosis", "nearest", "doi"]].to_string())
        print("\n", planted_benchmark(checks).round(2).to_string())
