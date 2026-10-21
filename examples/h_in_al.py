"""LitAudit on a literature query: hydrogen diffusivity in Al (lattice vs effective vs grain boundary).

Values are taken verbatim from the papers' abstracts (found with Valency Bond and OpenAlex, 2026-10-21).
Each source is a reported Arrhenius law (D0 m2/s, Q kJ/mol, valid T range if stated) or a single value at T.
Pairs are compared only where both sources are valid; comparing outside a fitted range is reported as
'not comparable' instead of being diagnosed, because Arrhenius extrapolation can fake a unit factor.

Run: python examples/h_in_al.py
"""
import math
import pathlib
import sys
from itertools import combinations

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from audit import diagnose, nearest  # noqa: E402

R = 8.314
SOURCES = [
    # name, doi, kind, D0 (m2/s), Q (kJ/mol), valid T range (K) or None if not in abstract, single (T, D m2/s)
    dict(name="Gunaydin 2008 (DFT-MD)", doi="PMID 18764553", kind="lattice",
         D0=1.8e-7, Q=0.12 * 96.485, T=(650, 850)),
    dict(name="JJAP 1998 (thermal evolution)", doi="10.1143/JJAP.37.930", kind="lattice",
         D0=3.0e-6, Q=30.0, T=None),
    dict(name="Corrosion 2013 (Al/Pd membrane, 1st charge)", doi="10.5006/0826", kind="effective (trapped)",
         point=(298, 1.6e-10 * 1e-4)),  # reported as 1.6e-10 cm2/s
]


def D(s, T):
    if "point" in s:
        return s["point"][1] if abs(T - s["point"][0]) < 5 else None
    return s["D0"] * math.exp(-s["Q"] * 1e3 / (R * T))


def valid(s, T):
    if "point" in s:
        return abs(T - s["point"][0]) < 5
    return s["T"] is None or s["T"][0] <= T <= s["T"][1]


def main():
    print(f"{'T (K)':>5}  {'source A':<44} {'source B':<44} {'log gap':>7}  verdict")
    for T in (298, 773):
        for a, b in combinations(SOURCES, 2):
            da, db = D(a, T), D(b, T)
            if da is None or db is None:
                continue
            gap = math.log10(da / db)
            if not (valid(a, T) and valid(b, T)):
                verdict = "not comparable: outside a fitted T range (extrapolation)"
            elif a["kind"] != b["kind"]:
                verdict = f"expected to differ: {a['kind']} vs {b['kind']} ({diagnose(gap, 'diffusivity')})"
            else:
                d = diagnose(gap, "diffusivity")
                verdict = d if d != "unexplained" else f"unexplained (nearest: {nearest(gap, 'diffusivity')})"
            print(f"{T:>5}  {a['name']:<44} {b['name']:<44} {gap:+7.2f}  {verdict}")
    print("\nValues used (m2/s):")
    for s in SOURCES:
        vals = ", ".join(f"{T} K: {D(s, T):.2e}" for T in (298, 773) if D(s, T) is not None)
        rng = s.get("T") or ("single point" if "point" in s else "range not stated")
        print(f"  {s['name']:<44} {s['kind']:<20} [{rng}]  {vals}   {s['doi']}")
    print("\nGrain-boundary diffusivity: no quantitative value in any abstract found. Ichimura et al.,\n"
          "Mater. Trans. 1991-93 (10.2320/matertrans1989.32.1109, .33.449, .34.404) report a 'grain\n"
          "boundary cross effect': fast diffusion along long straight GBs, trapping at GB junctions,\n"
          "so the apparent D depends on grain size. -> coverage gap, nothing to audit numerically.")


if __name__ == "__main__":
    main()
