"""Compare each value with independent references and diagnose any disagreement.

A check produces rows: check, db, doi, composition, property, value, reference, resid, tol, diagnosis, nearest, detail
- resid = log10(value / reference)
- tol = how close |resid| must be to a factor to name it; set per check from that check's own noise
- diagnosis = 'agree' | <named factor> | '<factor> or <factor>' (both fit within tol) | 'unexplained'
- nearest = for 'unexplained', the closest known factor and its distance (no auto-relabelling)
"""
import math

import numpy as np
import pandas as pd

AGREE = 0.3              # |resid| below this = consistent (lab-to-lab scatter is ~0.3 dex for conductivity)
TOL, TOL_MAX = 0.1, 0.25  # factor-match tolerance: 2x the check's noise, clipped to this range

L = math.log10
# Known unit/quantity confusions per property, as log10 of the factor they introduce.
FACTORS = {
    "ionic_conductivity": {"S/m stored as S/cm (x100)": 2, "mS/cm stored as S/cm (x1000)": 3,
                           "S/m vs mS/cm (x10)": 1, "sigma*T stored as sigma (~x298)": L(298)},
    "YS": {"GPa vs MPa (x1000)": 3, "ksi vs MPa (x6.9)": L(6.895)},
    "UTS": {"GPa vs MPa (x1000)": 3, "ksi vs MPa (x6.9)": L(6.895)},
    "HV": {"HV given in GPa (x102)": L(1 / 0.009807), "HV given in MPa (x9.8)": L(9.807)},
    "diffusivity": {"cm2/s vs m2/s (x10^4)": 4, "mm2/s vs m2/s (x10^6)": 6, "cm2/s vs mm2/s (x100)": 2},
}
# In a physics relation we know which side is which, so a mix-up has a direction: the factor is signed.
# HV_vs_YS resid = log10(YS / (c*HV*g/3)); density resid = log10(measured / calculated).
DIRECTED = {
    "HV_vs_YS": {"HV given in GPa (x102)": L(1 / 0.009807),   # HV number too small -> YS looks too high
                 "HV given in MPa (x9.8)": -L(9.807),         # HV number too big   -> YS looks too low
                 "YS: GPa stored as MPa (x1000)": -3,         # YS number too small
                 "YS: ksi stored as MPa (x6.9)": -L(6.895)},  # YS number too small
    "density_exp": {"measured kg/m3 stored as g/cm3 (x1000)": 3},
}


def _gaps(resid, prop):
    """(distance to factor, name) for every known factor of this property."""
    if prop in DIRECTED:
        return [(abs(resid - f), name) for name, f in DIRECTED[prop].items()]
    return [(abs(abs(resid) - f), name) for name, f in FACTORS.get(prop, {}).items()]


HV_MAX = 1500  # bulk metallic alloys stay below ~1500 HV; a larger stored number is not a Vickers number


def diagnose(resid, prop, tol=TOL, ref=None):
    """ref = the reference value, used to break ties the gap alone can't (HV in MPa vs YS in ksi)."""
    if abs(resid) < AGREE:
        return "agree"
    fits = [name for _, name in sorted(g for g in _gaps(resid, prop) if g[0] < tol)]
    if prop == "HV_vs_YS" and ref is not None and len(fits) > 1:
        hv_side = [f for f in fits if f.startswith("HV")]
        fits = hv_side if ref > HV_MAX else [f for f in fits if f not in hv_side] or fits
    return " or ".join(fits) if fits else "unexplained"


def noise_tol(resid):
    """Factor-match tolerance from the scatter of the comparisons that agree (robust sigma, x2)."""
    ok = resid[resid.abs() < AGREE]
    if len(ok) < 10:
        return TOL
    sigma = 1.4826 * (ok - ok.median()).abs().median()
    return float(np.clip(2 * sigma, TOL, TOL_MAX))


def nearest(resid, prop):
    """Closest known factor and how far off it is (shown for 'unexplained' so a human can judge)."""
    gaps = _gaps(resid, prop)
    if not gaps:
        return ""
    gap, name = min(gaps)
    return f"{name}, off by {gap:.2f}"


def _finish(out, check):
    out["check"] = check
    out["tol"] = noise_tol(out.resid)
    out["diagnosis"] = [diagnose(r, p, t, ref) for r, p, t, ref in zip(out.resid, out.property, out.tol, out.reference)]
    out["nearest"] = [nearest(r, p) if d == "unexplained" else ""
                      for r, p, d in zip(out.resid, out.property, out.diagnosis)]
    return out[["check", "db", "doi", "composition", "property", "value",
                "reference", "resid", "tol", "diagnosis", "nearest", "detail"]].reset_index(drop=True)


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
    Returns one row per (property, factor): n planted,
    recall = named alone, shortlist = named alone or as one of two candidates, flagged = any non-agree.
    """
    rng = np.random.default_rng(seed)
    clean = checks[checks.diagnosis == "agree"]
    rows = []
    for prop, factors in {**FACTORS, **DIRECTED}.items():
        base = clean[clean.property == prop]
        if base.empty:
            continue
        for name, f in factors.items():
            s = base.sample(frac=frac, random_state=int(rng.integers(1e9))) if len(base) > 10 else base
            # directed factors are planted in their physical direction; undirected ones either way
            sign = np.ones(len(s)) if prop in DIRECTED else rng.choice([-1, 1], size=len(s))
            # a hardness-unit error also changes the stored HV (the reference), not only the gap
            ref_mult = {"HV given in MPa (x9.8)": 9.807, "HV given in GPa (x102)": 0.009807}.get(name, 1)
            got = [diagnose(r + g * f, prop, t, ref * ref_mult)
                   for r, g, t, ref in zip(s.resid, sign, s.tol, s.reference)]
            rows.append({"property": prop, "factor": name, "n": len(s), "tol": s.tol.iloc[0],
                         "recall": np.mean([x == name for x in got]),
                         "shortlist": np.mean([name in x.split(" or ") and x.count(" or ") <= 1 for x in got]),
                         "flagged": np.mean([x != "agree" for x in got])})
    return pd.DataFrame(rows)


def run(df):
    return pd.concat([cross_db(df), relations(df)], ignore_index=True)


def report(checks, top=None):
    """Plain-text report: counts, flags (largest gap first) with verdict, planted-error benchmark."""
    flags = checks[checks.diagnosis != "agree"].sort_values("resid", key=abs, ascending=False)
    lines = [f"{len(checks)} comparisons, {len(flags)} flagged", ""]
    lines += [f"  {c:<17} {d:<32} {n:>4}" for (c, d), n in checks.groupby(["check", "diagnosis"]).size().items()]
    lines += ["", f"  {'composition':<26} {'value':>9} {'reference':>9}  {'log gap':>7}  verdict"]
    for r in flags.head(top).itertuples():
        verdict = r.diagnosis if r.diagnosis != "unexplained" else f"unexplained (nearest: {r.nearest})"
        lines.append(f"  {r.composition[:26]:<26} {r.value:9.3g} {r.reference:9.3g}  {r.resid:+7.2f}  {verdict}")
    lines += ["", f"  planted-error benchmark{'':<38}alone  in shortlist"]
    lines += [f"  {b.property:<19} {b.factor:<32} {b.recall:6.0%}  {b.shortlist:6.0%}"
              for b in planted_benchmark(checks).itertuples()]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from loaders import load_all
    print(report(run(load_all()), top=int(sys.argv[1]) if len(sys.argv) > 1 else None))
