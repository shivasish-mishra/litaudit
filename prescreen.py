"""Pick the flags worth tracing: those whose source has an open abstract (OpenAlex) stating a value in a matching unit.

Reads flags.json (written by audit.py); writes data/abstracts_openalex.json and data/trace_todo.json (flag ids to
pass to trace_flags.workflow.js as args.ids). Run: python prescreen.py
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).parent
UNITS = {"ionic_conductivity": r"(S\s?cm|S/cm|S\s?m|S/m|mS)", "YS": r"(MPa|GPa|ksi)", "UTS": r"(MPa|GPa|ksi)",
         "HV": r"(HV|Hv|hardness)", "HV_vs_YS": r"(MPa|GPa|HV|Hv)", "E": r"GPa"}


def abstract(doi):
    """OpenAlex abstract rebuilt from its inverted index; None if missing or only abstracting-service boilerplate."""
    if not doi.startswith("10."):
        return None
    try:
        w = json.load(urllib.request.urlopen("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi), timeout=30))
    except Exception:
        return None
    inv = w.get("abstract_inverted_index") or {}
    pos = {p: t for t, ps in inv.items() for p in ps}
    text = " ".join(pos[i] for i in sorted(pos))
    return None if not text or "ChemInform is a weekly Abstracting Service" in text else text


def main():
    flags = json.load(open(ROOT / "flags.json"))
    abstracts = {}
    for d in sorted({f["doi"] for f in flags}):
        abstracts[d] = abstract(d)
        time.sleep(0.1)
    todo = [f["id"] for f in flags if (a := abstracts.get(f["doi"])) and re.search(r"\d", a)
            and re.search(UNITS.get(f["property"], r"$^"), a)]
    json.dump(abstracts, open(ROOT / "data" / "abstracts_openalex.json", "w"), indent=0)
    json.dump(todo, open(ROOT / "data" / "trace_todo.json", "w"))
    print(f"{len(abstracts)} papers, {sum(map(bool, abstracts.values()))} with an open abstract; "
          f"{len(todo)} of {len(flags)} flags have a value with a matching unit in it: {todo}")


if __name__ == "__main__":
    main()
