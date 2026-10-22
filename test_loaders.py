"""Run: python test_loaders.py  (data checks are skipped if fetch_data.py hasn't run)."""
from loaders import DATA, COLUMNS, comp_key, load_all

# formula-unit scaling and element order must not matter
assert comp_key("Nd0.25Li0.25TaO3") == comp_key("Nd0.5Li0.5Ta2.0O6.0")
assert comp_key("Li7La3Zr2O12") == comp_key("La3Li7O12Zr2")
assert comp_key("Al1 Co1 Cr1 Fe1 Ni1") == comp_key("AlCoCrFeNi")
assert comp_key("Li7La3Zr2O12") != comp_key("Li6.5La3Zr1.75Te0.25O12")
# bracket multipliers count (a bug that once merged different pseudo-binary compositions)
assert comp_key("(YPO4)0.8(Li3PO4)0.2") != comp_key("(YPO4)0.5(Li3PO4)0.5")
assert comp_key("LiTi2(PO4)3") == comp_key("LiTi2P3O12")
assert comp_key('"(Li2S)0.5 ((Ga2S3)0.1 (GeS2)0.9)0.5"') == comp_key("Li1Ga0.1S1.55Ge0.45")
assert comp_key('"((Li2S)0.6 (SiS2)0.4)95 (Li4SiO4)5"') == comp_key("Li134Si43S133O20")

if all((DATA / f).exists() for f in ("liverpool.csv", "obelix.csv", "mpea.csv")):
    df = load_all()
    assert list(df.columns) == COLUMNS
    assert set(df.db) == {"liverpool", "obelix", "mpea"}
    assert (df.value > 0).all()
    # verified case I16 (Mizumoto 1999): Nd entry present in both databases, ~100x apart
    nd = df[(df.doi == "10.1016/s0167-2738(98)00414-7") & (df.comp_key == comp_key("Nd0.25Li0.25TaO3"))]
    vals = dict(zip(nd.db, nd.value))
    assert vals == {"liverpool": 1.91e-6, "obelix": 1.31e-8}, vals
    print(f"ok ({len(df)} values loaded)")
else:
    print("ok (unit checks only; run fetch_data.py for data checks)")

# a leading coefficient must fail loudly, not be dropped or applied to the previous element
for bad in ("0.75Li2S 0.25P2S5", "Li2S 25P2S5"):
    try:
        comp_key(bad)
        raise AssertionError(bad)
    except ValueError:
        pass
if (DATA / "liverpool.csv").exists():
    keys = df.db + ":" + df.row_id + ":" + df.property
    assert keys.is_unique, keys[keys.duplicated()].tolist()
