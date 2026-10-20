"""Run: python test_loaders.py  (data checks are skipped if fetch_data.py hasn't run)."""
from loaders import DATA, COLUMNS, comp_key, load_all

# formula-unit scaling and element order must not matter
assert comp_key("Nd0.25Li0.25TaO3") == comp_key("Nd0.5Li0.5Ta2.0O6.0")
assert comp_key("Li7La3Zr2O12") == comp_key("La3Li7O12Zr2")
assert comp_key("Al1 Co1 Cr1 Fe1 Ni1") == comp_key("AlCoCrFeNi")
assert comp_key("Li7La3Zr2O12") != comp_key("Li6.5La3Zr1.75Te0.25O12")

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
