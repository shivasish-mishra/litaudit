"""Load the source databases into one long table: one row per (entry, property) value.

Columns: db, row_id, doi, composition, comp_key, property, value, unit, T_K, T_assumed, condition
- value is in the property's canonical unit (see UNITS); nothing is corrected here.
- comp_key is a normalised composition (atom fractions, sorted) so the same material
  matches across databases whatever its formula-unit scaling.
"""
import io
import pathlib
import re
from collections import Counter

import pandas as pd

DATA = pathlib.Path(__file__).parent / "data"
UNITS = {"ionic_conductivity": "S/cm", "HV": "HV", "YS": "MPa", "UTS": "MPa",
         "E": "GPa", "density_exp": "g/cm3", "density_calc": "g/cm3"}
COLUMNS = ["db", "row_id", "doi", "composition", "comp_key", "property",
           "value", "unit", "T_K", "T_assumed", "condition"]
ROOM_T_K = 298.15


_TOKEN = re.compile(r"\s*(?:([A-Z][a-z]?)|([(\[])|([)\]])|(\d*\.?\d+))")


def parse_formula(formula):
    """Element counts of a formula, honouring (nested) bracket multipliers:
    '(YPO4)0.8(Li3PO4)0.2' -> Y 0.8, P 1.0, O 4.0, Li 0.6; quotes and spaces are ignored."""
    s = str(formula).replace('"', "").strip()
    stack, pos = [Counter()], 0
    last = None  # what a following number multiplies: an element name or a just-closed group
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise ValueError(f"cannot parse formula {formula!r} at {s[pos:]!r}")
        start, pos = pos, m.end()
        el, opn, cls, num = m.groups()
        if el:
            stack[-1][el] += 1.0
            last = ("el", el)
        elif opn:
            stack.append(Counter())
            last = None
        elif cls:
            group = stack.pop()
            stack[-1].update(group)
            last = ("grp", group)
        else:  # a number multiplies the element or bracket right before it (no space in between)
            if not last or s[start].isspace():
                raise ValueError(f"leading coefficient or stray number in formula {formula!r}")
            n = float(num)
            if last[0] == "el":
                stack[-1][last[1]] += n - 1.0
            else:
                for k, v in last[1].items():
                    stack[-1][k] += v * (n - 1.0)
            last = None
    if len(stack) != 1:
        raise ValueError(f"unbalanced brackets in {formula!r}")
    return stack[0]


def comp_key(formula):
    """'Nd0.25Li0.25TaO3' and 'Nd0.5Li0.5Ta2O6' -> the same key; '(YPO4)0.8(Li3PO4)0.2' keeps its ratio."""
    counts = parse_formula(formula)
    total = sum(counts.values())
    if not total:
        return ""
    return " ".join(f"{el}{counts[el] / total:.4f}" for el in sorted(counts))


def _doi(s):
    return str(s).strip().lower().removeprefix("https://doi.org/")


def load_liverpool(path=DATA / "liverpool.csv"):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("ID,"))  # licence text above the header
    df = pd.read_csv(io.StringIO("\n".join(lines[start:])))
    # IDs are not unique in the source (922 appears twice): suffix repeats so every entry has its own key
    row_id = df["ID"].astype(str) + df.groupby("ID").cumcount().map(lambda n: f".{n}" if n else "")
    return pd.DataFrame({
        "db": "liverpool", "row_id": row_id, "doi": df["source"].map(_doi),
        "composition": df["composition"], "comp_key": df["composition"].map(comp_key),
        "property": "ionic_conductivity", "value": pd.to_numeric(df["target"], errors="coerce"),
        "unit": "S/cm", "T_K": df["temperature"] + 273.15, "T_assumed": False,
        "condition": df["family"],
    })


def load_obelix(path=DATA / "obelix.csv"):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "db": "obelix", "row_id": df["ID"].astype(str), "doi": df["DOI"].map(_doi),
        "composition": df["Composition"], "comp_key": df["Composition"].map(comp_key),
        "property": "ionic_conductivity",
        "value": pd.to_numeric(df["Ionic conductivity (S cm-1)"], errors="coerce"),
        "unit": "S/cm", "T_K": ROOM_T_K, "T_assumed": True,  # OBELiX is room temperature by definition
        # space group separates polymorphs of one composition (tetragonal vs cubic LLZO differ ~100x)
        "condition": "SG " + df["Space group number"].astype(str),
    })


def load_mpea(path=DATA / "mpea.csv"):
    df = pd.read_csv(path)
    cols = {"PROPERTY: HV": "HV", "PROPERTY: YS (MPa)": "YS", "PROPERTY: UTS (MPa)": "UTS",
            "PROPERTY: Exp. Young modulus (GPa)": "E",
            "PROPERTY: Exp. Density (g/cm$^3$)": "density_exp",
            "PROPERTY: Calculated Density (g/cm$^3$)": "density_calc"}
    T = pd.to_numeric(df["PROPERTY: Test temperature ($^\\circ$C)"], errors="coerce")
    base = pd.DataFrame({
        "db": "mpea", "row_id": df.index.astype(str), "doi": df["REFERENCE: doi"].map(_doi),
        "composition": df["FORMULA"], "comp_key": df["FORMULA"].map(comp_key),
        "T_K": T.fillna(25) + 273.15, "T_assumed": T.isna(),
        # test type (C/T) + processing: YS in compression and tension aren't comparable
        "condition": df["PROPERTY: Type of test"].fillna("") + "|" + df["PROPERTY: Processing method"].fillna(""),
    })
    parts = []
    for col, prop in cols.items():
        p = base.copy()
        p["property"], p["unit"] = prop, UNITS[prop]
        p["value"] = pd.to_numeric(df[col], errors="coerce")
        parts.append(p)
    return pd.concat(parts)


def load_all():
    df = pd.concat([load_liverpool(), load_obelix(), load_mpea()], ignore_index=True)
    return df.dropna(subset=["value"])[COLUMNS].reset_index(drop=True)


if __name__ == "__main__":
    df = load_all()
    print(df.groupby(["db", "property"]).size().to_string())
    print(f"\n{len(df)} values, {df.doi.nunique()} DOIs, {df.comp_key.nunique()} compositions")
