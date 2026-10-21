"""Run: python test_audit.py  (data checks need fetch_data.py first)."""
import math

from audit import diagnose, nearest, run
from loaders import DATA

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
    # verified against the papers (see litaudit_pitch_and_plan.md): all three must be flagged
    for doi in ("10.1016/s0167-2738(98)00414-7", "10.1016/j.jpowsour.2013.03.166", "10.1063/1.2734517"):
        assert (checks[checks.doi == doi].diagnosis != "agree").any(), doi
    nd = checks[(checks.doi == "10.1016/s0167-2738(98)00414-7") & (checks.composition == "Nd0.25Li0.25TaO3")]
    assert "x100" in nd.nearest.iloc[0], nd
    print(f"ok ({len(checks)} comparisons)")
else:
    print("ok (unit checks only)")
