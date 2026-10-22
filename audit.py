"""Compare each value with independent references and diagnose any disagreement.

A check produces rows: check, db, doi, composition, property, value, reference, resid, agree, tol,
diagnosis, nearest, key_a, key_b, attributable, detail
- resid = log10(value / reference)
- agree, tol = from the check's own robust scatter sigma: agree = max(AGREE, 3 sigma), tol = clip(2 sigma)
- diagnosis = 'agree' | <named factor> | '<factor> or <factor>' (both fit within tol) | 'unexplained'
- nearest = for 'unexplained', the closest known factor and its distance (no auto-relabelling)
- key_a / key_b = the database entries on the value / reference side ('db:row_id:property'); key_b is ''
  when the reference is a fit or a median of other papers
- attributable = True when a disagreement points at key_a specifically (the reference is built from
  several other values), False when it is symmetric (two values, either could be wrong)
"""
import math

import numpy as np
import pandas as pd

AGREE = 0.3              # lower bound of the agreement band (lab-to-lab scatter ~0.3 dex for conductivity)
TOL, TOL_MAX = 0.1, 0.25  # factor-match tolerance: 2x the check's noise, clipped to this range
NAME_SIGMA_MAX = 0.2      # a check names causes only if its scatter resolves the 1-dex factor ladder (>= 5 sigma);
                          # noisier checks (papers vs papers: ~0.6 dex) still flag, but report 'unexplained'
K_B = 8.617333e-5        # eV/K

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
T_SLIP = "temperature in K stored as degC"  # Arrhenius-only diagnosis (T_K too high by 273.15)


def _gaps(resid, prop):
    """(distance to factor, name) for every known factor of this property."""
    if prop in DIRECTED:
        return [(abs(resid - f), name) for name, f in DIRECTED[prop].items()]
    return [(abs(abs(resid) - f), name) for name, f in FACTORS.get(prop, {}).items()]


HV_MAX = 1500  # bulk metallic alloys stay below ~1500 HV; a larger stored number is not a Vickers number


def diagnose(resid, prop, tol=TOL, ref=None, agree=AGREE):
    """ref = the reference value, used to break ties the gap alone can't (HV in MPa vs YS in ksi)."""
    if abs(resid) < agree:
        return "agree"
    fits = [name for _, name in sorted(g for g in _gaps(resid, prop) if g[0] < tol)]
    if prop == "HV_vs_YS" and ref is not None and len(fits) > 1:
        hv_side = [f for f in fits if f.startswith("HV")]
        fits = hv_side if ref > HV_MAX else [f for f in fits if f not in hv_side] or fits
    return " or ".join(fits) if fits else "unexplained"


def noise(resid):
    """(agree band, factor tolerance) from the check's robust scatter (MAD sigma of all its residuals).
    Tolerance 0 = this check is too noisy to name a cause (it can still flag)."""
    r = pd.Series(resid).dropna()
    if len(r) < 10:
        return AGREE, TOL
    sigma = 1.4826 * (r - r.median()).abs().median()
    tol = float(np.clip(2 * sigma, TOL, TOL_MAX)) if sigma <= NAME_SIGMA_MAX else 0.0
    return float(max(AGREE, 3 * sigma)), tol


def nearest(resid, prop):
    """Closest known factor and how far off it is (shown for 'unexplained' so a human can judge)."""
    gaps = _gaps(resid, prop)
    if not gaps:
        return ""
    gap, name = min(gaps)
    return f"{name}, off by {gap:.2f}"


COLS = ["check", "db", "doi", "composition", "property", "value", "reference", "resid", "agree", "tol",
        "diagnosis", "nearest", "key_a", "key_b", "attributable", "detail"]


def _key(db, row_id, prop):
    return db + ":" + row_id.astype(str) + ":" + prop


def _finish(out, check, band=None):
    out = out.reset_index(drop=True)
    out["check"] = check
    out["agree"], out["tol"] = band or noise(out.resid)
    out["diagnosis"] = [diagnose(r, p, t, ref, a) for r, p, t, ref, a in
                        zip(out.resid, out.property, out.tol, out.reference, out.agree)]
    out["nearest"] = [nearest(r, p) if d == "unexplained" else ""
                      for r, p, d in zip(out.resid, out.property, out.diagnosis)]
    return out[COLS]


def cross_db(df, max_dT=10):
    """Same paper + same composition + same property in two databases, at about the same T (symmetric)."""
    m = df.merge(df, on=["doi", "comp_key", "property"])
    m = m[(m.db_x < m.db_y) & ((m.T_K_x - m.T_K_y).abs() <= max_dT)]
    out = pd.DataFrame({
        "db": m.db_x + " vs " + m.db_y, "doi": m.doi, "composition": m.composition_x,
        "property": m.property, "value": m.value_x, "reference": m.value_y,
        "resid": np.log10(m.value_x / m.value_y),
        "key_a": _key(m.db_x, m.row_id_x, m.property), "key_b": _key(m.db_y, m.row_id_y, m.property),
        "attributable": False, "detail": m.row_id_x + " / " + m.row_id_y,
    })
    return _finish(out, "cross_db")


def _interp(x0, xs, ys):
    """Linear interpolation of y at x0 between its nearest neighbours on each side; nan if x0 is outside."""
    lo, hi = xs < x0, xs > x0
    if not lo.any() or not hi.any():
        return np.nan
    i, j = np.argmax(np.where(lo, xs, -np.inf)), np.argmin(np.where(hi, xs, np.inf))
    return ys[i] + (ys[j] - ys[i]) * (x0 - xs[i]) / (xs[j] - xs[i])


def _extrap(x0, xs, ys):
    """Value at x0 of the line through the two points nearest to x0 (distinct x); nan if fewer than two, or if
    x0 lies more than twice their own spacing away (a long extrapolation, e.g. a room-temperature point
    predicted from a high-temperature regime, is not a fair test; 2x allows the naturally wider 1000/T
    spacing at the cold end of an evenly stepped series)."""
    ux = np.unique(xs)
    if len(ux) < 2:
        return np.nan
    near = ux[np.argsort(np.abs(ux - x0))[:2]]
    if abs(x0 - near[0]) > 2 * abs(near[1] - near[0]):
        return np.nan
    y_at = [ys[xs == v].mean() for v in near]
    return y_at[0] + (y_at[1] - y_at[0]) * (x0 - near[0]) / (near[1] - near[0])


def _arrhenius_series(g):
    """One paper's series: x = 1000/T, y = log10(sigma*T), per entry. Interior points only are judgeable."""
    return 1000 / g.T_K.values, np.log10(g.value.values * g.T_K.values)


def arrhenius(df, prop="ionic_conductivity", min_T=3):
    """Within one paper's temperature series for one composition, check each point against its neighbours.

    In Arrhenius coordinates (log10(sigma*T) vs 1000/T) an interior point is predicted by linear
    interpolation between its nearest lower- and higher-temperature neighbours: exact for an Arrhenius
    line and tolerant of smooth curvature. End points are judged by a local line through their two
    nearest neighbours, but only within 2 neighbour spacings and only in series of >= 4 temperatures.
    Culprits are removed one at a time by a removal test (whose removal leaves the most consistent
    series), so a bad point does not drag its neighbours down; removed points that fit the cleaned series
    are put back. A culprit beyond the testable range is judged against a line through the rest and flagged
    without a named cause. 3-temperature series are symmetric (not attributable).
    A flagged point that fits once its T is read as kelvin (T_K - 273.15) is diagnosed T_SLIP.
    """
    c = df[df.property == prop]
    # condition (Liverpool: material family) keeps e.g. a glass and its glass-ceramic in separate series
    groups = [(k, g.reset_index(drop=True)) for k, g in c.groupby(["db", "doi", "comp_key", "condition"])
              if g.T_K.nunique() >= min_T]

    def resids(x, y, active):
        r = np.full(len(x), np.nan)
        for i in np.flatnonzero(active):
            others = active & (x != x[i])
            r[i] = y[i] - _interp(x[i], x[others], y[others])
        return r

    # pass 1: plain residuals of every judgeable point -> the check's noise band
    pass1 = np.concatenate([resids(*_arrhenius_series(g), np.ones(len(g), bool)) for _, g in groups] or [[]])
    band = noise(pd.Series(pass1).dropna())

    def own(i, x, y, active):
        """Residual of point i against the active others: interpolation if inside, else a local line
        through its two nearest neighbours (only used for series with >= 4 temperatures)."""
        others = active & (x != x[i])
        ref = _interp(x[i], x[others], y[others])
        if ref != ref:
            ref = _extrap(x[i], x[others], y[others])
        return y[i] - ref, ref

    def tslip_gap(i, x, y, T, val, active):
        """Gap of point i if its stored temperature was really kelvin (T_K - 273.15), against the active others."""
        t_alt = T[i] - 273.15
        if t_alt <= 100:
            return np.nan
        others = active & (np.arange(len(x)) != i)
        xa = 1000 / t_alt
        ref = _interp(xa, x[others], y[others])
        if ref != ref:
            ref = _extrap(xa, x[others], y[others])
        return math.log10(val[i] * t_alt) - ref

    rows = []
    for (db, doi, ck, cond), g in groups:
        x, y = _arrhenius_series(g)
        T, val, idx = g.T_K.values, g.value.values, np.arange(len(g))
        n_t = len(set(x))
        active, out_r, out_ref = np.ones(len(g), bool), np.full(len(g), np.nan), np.full(len(g), np.nan)
        forced = {}  # culprits beyond the testable range: i -> T_SLIP, or "estimate" (judged on a fitted line)
        # pass 2 (>= 4 temperatures, while the series is inconsistent): blame the point whose removal
        # leaves the most self-consistent series
        while n_t >= 4 and len(set(x[active])) >= 4:
            if not np.nanmax(np.abs(resids(x, y, active)), initial=0) >= band[0]:
                break
            score = []
            for i in np.flatnonzero(active):
                a2 = active.copy()
                a2[i] = False
                # every remaining point, ends included, so dropping an end point is not a free way to look clean
                r2 = np.array([own(j, x, y, a2)[0] for j in np.flatnonzero(a2)])
                score.append((int(np.sum(np.abs(r2) >= band[0])), float(np.nansum(r2 ** 2)), i))
            i = min(score)[2]
            r, _ = own(i, x, y, active)
            if r == r and abs(r) < band[0]:
                break
            active[i] = False  # the culprit (if beyond the testable range, it is judged below)

        def against(i):
            """Point i vs the cleaned series; beyond its range, vs a line through it (an estimate)."""
            r, ref = own(i, x, y, active)
            if r != r:
                ref = np.polyval(np.polyfit(x[active], y[active], 1), x[i])
                r = y[i] - ref
            return r, ref

        # the greedy removal can blame a good point next to bad ones: put back every removed point that fits
        changed = True
        while changed:
            changed = False
            for i in np.flatnonzero(~active):
                if abs(against(i)[0]) < band[0]:
                    active[i], changed = True, True
        for i in np.flatnonzero(~active):
            out_r[i], out_ref[i] = against(i)
            if own(i, x, y, active)[0] != own(i, x, y, active)[0]:  # only the line estimate reaches it
                forced[i] = T_SLIP if abs(tslip_gap(i, x, y, T, val, active)) < band[0] else "estimate"
        for i in np.flatnonzero(active):  # remaining points: interior by interpolation, ends by local line
            others = active & (x != x[i])
            if n_t >= 4 or _interp(x[i], x[others], y[others]) == _interp(x[i], x[others], y[others]):
                out_r[i], out_ref[i] = own(i, x, y, active)
        ea = -np.polyfit(x[active], y[active], 1)[0] * 1000 * K_B * math.log(10) if active.sum() >= 2 else np.nan
        for i, row in g.iterrows():
            if np.isnan(out_r[i]):
                continue  # not judgeable (end of a 3-temperature series, or beyond the extrapolation cap)
            rows.append({"db": db, "doi": doi, "composition": row.composition, "property": prop,
                         "value": row.value, "reference": 10 ** out_ref[i] / row.T_K, "resid": out_r[i],
                         "tslip": tslip_gap(i, x, y, T, val, active), "forced": forced.get(i, ""),
                         "key_a": f"{db}:{row.row_id}:{prop}", "key_b": "",
                         "attributable": n_t >= 4 and forced.get(i) != "estimate",
                         "detail": f"T={row.T_K:.0f} K, {n_t} temperatures, series Ea {ea:.2f} eV" +
                                   (", beyond the series: vs a line through the rest" if i in forced else "")})
    if not rows:
        return pd.DataFrame(columns=COLS)
    out = pd.DataFrame(rows)
    tslip, forced = out.pop("tslip"), out.pop("forced")
    res = _finish(out, "arrhenius", band)
    # a flagged point that fits once its temperature is read as kelvin: name the slip (alongside any unit
    # factor that also fits - both explanations are then reported)
    fits = (res.diagnosis != "agree") & (tslip.abs() < res.agree)
    res.loc[fits & (res.diagnosis == "unexplained"), "diagnosis"] = T_SLIP
    both = fits & ~res.diagnosis.isin([T_SLIP])
    res.loc[both, "diagnosis"] = res.loc[both, "diagnosis"] + " or " + T_SLIP
    res.loc[forced == T_SLIP, "diagnosis"] = T_SLIP
    est = (forced == "estimate") & ~res.diagnosis.isin(["agree", T_SLIP])  # extrapolated: flag, never name
    res.loc[est, "diagnosis"] = "unexplained"
    res.loc[est, "nearest"] = [nearest(r, prop) for r in res.resid[est]]
    res.loc[res.diagnosis.str.contains(T_SLIP, regex=False), "nearest"] = ""
    return res


STRENGTH = {"YS", "UTS"}  # the only properties whose value depends on the test type (compression vs tension)


def cross_paper(df, rt_K=10):
    """Same composition (and condition) reported by different papers in one database, near RT.

    Each entry is compared with the median of the OTHER papers' medians, so a single slipped entry is caught
    even when its paper has several; with >= 3 papers reporting it the entry is attributable, with 2 it is
    symmetric. The noise band counts one residual per paper, so many-entry papers do not set it alone.
    """
    d = df[(df.T_K - 298.15).abs() <= rt_K].copy()
    d["lg"] = np.log10(d.value)
    # MPEA conditions are "test type|processing"; drop the test type where it cannot matter
    d["cond"] = d.condition.where(d.property.isin(STRENGTH), d.condition.str.split("|").str[-1])
    rows = []
    for (db, prop, ck, cond), g in d.groupby(["db", "property", "comp_key", "cond"]):
        paper = g.groupby("doi").lg.median()
        if len(paper) < 2:
            continue
        for r in g.itertuples():
            others = paper.drop(r.doi)
            ref = 10 ** others.median()
            rows.append({"db": db, "doi": r.doi, "composition": r.composition, "property": prop,
                         "value": r.value, "reference": ref, "resid": math.log10(r.value / ref),
                         "key_a": f"{db}:{r.row_id}:{prop}", "key_b": "", "attributable": len(paper) >= 3,
                         "grp": f"{ck}|{cond}", "detail": f"vs median of {len(others)} other paper(s)"})
    if not rows:
        return pd.DataFrame(columns=COLS)
    out = pd.DataFrame(rows)
    # the agreement band is per property: scatter between papers differs a lot between properties
    return pd.concat([_finish(g, "cross_paper", noise(g.groupby(["grp", "doi"]).resid.median()))
                      for _, g in out.groupby("property")], ignore_index=True)


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
        "key_a": "mpea:" + t.row_id.astype(str) + ":YS", "key_b": "mpea:" + t.row_id.astype(str) + ":HV",
        "attributable": False, "detail": "YS (MPa) vs HV, test " + t.test,
    }), "relation_tabor"))

    # Measured vs calculated (rule-of-mixtures) density; porosity only lowers the measured value.
    d = rows.dropna(subset=["density_exp", "density_calc"])
    parts.append(_finish(pd.DataFrame({
        "db": "mpea", "doi": d.doi, "composition": d.composition, "property": "density_exp",
        "value": d.density_exp, "reference": d.density_calc,
        "resid": np.log10(d.density_exp / d.density_calc),
        "key_a": "mpea:" + d.row_id.astype(str) + ":density_exp",
        "key_b": "mpea:" + d.row_id.astype(str) + ":density_calc",
        "attributable": False, "detail": "measured vs calculated",
    }), "relation_density"))
    return pd.concat(parts, ignore_index=True)


def run(df):
    parts = [cross_db(df), arrhenius(df), cross_paper(df), relations(df)]
    return pd.concat([p for p in parts if len(p)], ignore_index=True)


def entry_verdicts(checks):
    """Combine all checks per database entry: which entries are suspect, and how firmly.

    suspect   = flagged by an attributable check (the reference is several other values), or the unconfirmed side
                of a symmetric disagreement whose other side is confirmed
    ambiguous = flagged only in symmetric comparisons that cannot be resolved
    clean     = checked and never flagged, or every disagreement it took part in was resolved against the partner
    Confirmed = passes an attributable check against other sources (not its own series: that cannot see a
    scale error) whose agreement band is narrower than the disagreement, and is never flagged by one.
    """
    long = pd.concat([
        checks.assign(key=checks.key_a, side_attr=checks.attributable),
        checks[checks.key_b != ""].assign(key=lambda c: c.key_b, side_attr=False),
    ])
    long["flag"] = long.diagnosis != "agree"
    per = long.groupby("key").agg(n_checks=("flag", "size"), n_flags=("flag", "sum"),
                                  attr_flag=("flag", lambda f: bool((f & long.loc[f.index, "side_attr"]).any())))
    per["verdict"] = np.where(per.attr_flag, "suspect", np.where(per.n_flags > 0, "ambiguous", "clean"))
    conf = checks[checks.attributable & (checks.diagnosis == "agree") & (checks.check != "arrhenius")]
    band = conf.groupby("key_a").agree.min()

    def confirmed(k, gap):
        return band.get(k, np.inf) < gap and not per.at[k, "attr_flag"]

    sym = checks[(~checks.attributable) & (checks.diagnosis != "agree") & (checks.key_b != "")]
    resolved = {}  # key -> for each of its symmetric disagreements: was it pinned on the partner?
    for a, b, gap in zip(sym.key_a, sym.key_b, sym.resid.abs()):
        ca, cb = confirmed(a, gap), confirmed(b, gap)
        bad = b if ca and not cb else a if cb and not ca else None  # both or neither confirmed: unresolved
        for k, other in ((a, b), (b, a)):
            resolved.setdefault(k, []).append(bad == other)
        if bad and per.at[bad, "verdict"] == "ambiguous":
            per.at[bad, "verdict"] = "suspect"
    for k, res in resolved.items():  # cleared only if ALL its flags were disagreements pinned on the partner
        if per.at[k, "verdict"] == "ambiguous" and len(res) == per.at[k, "n_flags"] and all(res):
            per.at[k, "verdict"] = "clean"
    return per.reset_index()


# Value-level corruption for each named factor: (property whose stored value is corrupted, multiplier).
# Directions follow the physics of the slip (e.g. S/m read as S/cm makes the stored number 100x too big).
PLANT = {
    "S/m stored as S/cm (x100)": ("ionic_conductivity", 100.0),
    "mS/cm stored as S/cm (x1000)": ("ionic_conductivity", 1000.0),
    "S/m vs mS/cm (x10)": ("ionic_conductivity", 10.0),
    "sigma*T stored as sigma (~x298)": ("ionic_conductivity", 298.0),
    "HV given in GPa (x102)": ("HV", 0.009807),
    "HV given in MPa (x9.8)": ("HV", 9.807),
    "YS: GPa stored as MPa (x1000)": ("YS", 1e-3),
    "YS: ksi stored as MPa (x6.9)": ("YS", 1 / 6.895),
    "measured kg/m3 stored as g/cm3 (x1000)": ("density_exp", 1000.0),
}
# the same slip under the name an undirected check (cross_paper) gives it
SAME = {"YS: GPa stored as MPa (x1000)": "GPa vs MPa (x1000)", "YS: ksi stored as MPa (x6.9)": "ksi vs MPa (x6.9)"}


def planted_benchmark(df, frac=0.05, seeds=(0, 1, 2)):
    """End-to-end: corrupt stored values, re-run every check, ask whether the corrupted entries are caught.

    Only entries that some check covers and that are not already flagged can be fairly tested, so the sample is
    drawn from those and the coverage is reported separately. Per factor:
      flagged   = corrupted entry flagged by at least one check
      named     = the factor named alone in at least one check that involves the entry
      shortlist = named alone or as one of two candidates
      suspect   = entry-level verdict 'suspect' (pinned on this entry, not just a disagreement)
      collateral = share of NON-corrupted entries that become newly flagged (false alarms the corruption causes)
    """
    base = run(df)
    base_flagged = set(pd.concat([base.key_a, base.key_b])[
        pd.concat([base.diagnosis, base.diagnosis]) != "agree"])
    covered = set(base.key_a) | set(base.key_b) - {""}
    df = df.assign(key=df.db + ":" + df.row_id.astype(str) + ":" + df.property)
    rows = []
    for name, (prop, mult) in PLANT.items():
        pool = df[(df.property == prop) & df.key.isin(covered - base_flagged)]
        names = {name, SAME.get(name)}
        if pool.empty:
            continue
        stats = {k: [] for k in ("flagged", "named", "shortlist", "suspect", "collateral")}
        for seed in seeds:
            pick = pool.sample(frac=frac, random_state=seed) if len(pool) * frac >= 5 else pool.sample(
                n=min(5, len(pool)), random_state=seed)
            bad = df.copy()
            bad.loc[pick.index, "value"] *= mult
            res = run(bad.drop(columns="key"))
            verdict = entry_verdicts(res).set_index("key").verdict
            for k in pick.key:
                inv = res[(res.key_a == k) | (res.key_b == k)]
                diags = inv.diagnosis.tolist()
                stats["flagged"].append(any(d != "agree" for d in diags))
                stats["named"].append(any(d in names for d in diags))
                stats["shortlist"].append(any(names & set(d.split(" or ")) and d.count(" or ") <= 1 for d in diags))
                stats["suspect"].append(verdict.get(k) == "suspect")
            now = set(pd.concat([res.key_a, res.key_b])[pd.concat([res.diagnosis, res.diagnosis]) != "agree"])
            clean = covered - set(pick.key) - base_flagged
            stats["collateral"].append(len((now - base_flagged) & clean) / max(1, len(clean)))
        rows.append({"property": prop, "factor": name, "n": len(stats["flagged"]),
                     **{k: float(np.mean(v)) for k, v in stats.items()}})
    return pd.DataFrame(rows)


def coverage(df, checks):
    """Share of each property's stored values that at least one check looks at."""
    covered = set(checks.key_a) | set(checks.key_b)
    keys = df.db + ":" + df.row_id.astype(str) + ":" + df.property
    return keys.isin(covered).groupby([df.db, df.property]).mean()


def report(checks, top=None, df=None, only=None):
    """Plain-text report: counts, flags (largest gap first; only one check if `only`) with verdict, entry verdicts,
    coverage and the end-to-end benchmark (the last two need `df`)."""
    flags = checks[checks.diagnosis != "agree"].sort_values("resid", key=abs, ascending=False)
    lines = [f"{len(checks)} comparisons, {len(flags)} flagged" + (f" (listing {only} only)" if only else ""), ""]
    if only:
        flags = flags[flags.check == only]
    lines += [f"  {c:<17} {d:<34} {n:>4}" for (c, d), n in checks.groupby(["check", "diagnosis"]).size().items()]
    lines += ["", f"  {'check':<11} {'composition':<26} {'value':>9} {'reference':>9}  {'log gap':>7}  verdict"]
    for r in flags.head(top).itertuples():
        verdict = r.diagnosis if r.diagnosis != "unexplained" else f"unexplained (nearest: {r.nearest})"
        lines.append(f"  {r.check[:11]:<11} {r.composition[:26]:<26} {r.value:9.3g} {r.reference:9.3g}  "
                     f"{r.resid:+7.2f}  {verdict}")
    ev = entry_verdicts(checks).verdict.value_counts()
    lines += ["", "  entries: " + ", ".join(f"{k} {v}" for k, v in ev.items())]
    if df is not None:
        lines += ["", "  coverage (share of stored values checked):"]
        lines += [f"  {db:<10} {p:<19} {v:5.0%}" for (db, p), v in coverage(df, checks).items()]
        lines += ["", f"  planted-error benchmark (end-to-end)  {'flagged':>8} {'named':>6} {'short':>6} "
                      f"{'suspect':>8} {'collat.':>8}"]
        lines += [f"  {b.factor:<38} {b.flagged:8.0%} {b.named:6.0%} {b.shortlist:6.0%} {b.suspect:8.0%} "
                  f"{b.collateral:8.1%}" for b in planted_benchmark(df).itertuples()]
    return "\n".join(lines)


def flag_id(check, key_a, key_b):
    """Stable id of a comparison: check/entry[/partner row]; unchanged when other flags come or go."""
    return f"{check}/{key_a}" + (f"/{key_b.rsplit(':', 1)[0]}" if key_b else "")


def write_flags(checks, path=None):
    """Every flag, largest gap first, as the input of the agent trace workflow."""
    import json
    import pathlib
    path = path or pathlib.Path(__file__).parent / "flags.json"
    f = checks[checks.diagnosis != "agree"].sort_values("resid", key=abs, ascending=False).reset_index(drop=True)
    items = [{"id": flag_id(r.check, r.key_a, r.key_b), "check": r.check, "db": r.db, "doi": r.doi, "composition": r.composition,
              "property": r.property, "value": float(f"{r.value:.4g}"), "reference": float(f"{r.reference:.4g}"),
              "log10_gap": round(float(r.resid), 2), "diagnosis": r.diagnosis, "nearest": r.nearest,
              "detail": r.detail, "attributable": bool(r.attributable)} for i, r in f.iterrows()]
    with open(path, "w") as fh:
        json.dump(items, fh, indent=1)


if __name__ == "__main__":
    import sys
    from loaders import load_all
    data = load_all()  # usage: python audit.py [top N flags] [check name, e.g. cross_db]
    checks = run(data)
    write_flags(checks)
    print(report(checks, top=int(sys.argv[1]) if len(sys.argv) > 1 else None, df=data,
                 only=sys.argv[2] if len(sys.argv) > 2 else None))
