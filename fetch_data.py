"""Download the three source databases into data/ and check they are the versions the results were made with.
Never commit data/ (Liverpool licence)."""
import hashlib
import pathlib
import urllib.request

DATA = pathlib.Path(__file__).parent / "data"

SOURCES = {  # name: (url, md5 of the version used for the results; a mismatch renumbers flags and shifts numbers)
    # Hargreaves et al., npj Comput. Mater. 9, 9 (2023). Free for academic use; cite the University of Liverpool.
    "liverpool.csv": ("http://pcwww.liv.ac.uk/~msd30/lmds/LiIonDatabase.csv", "82905eaea60cb02bf7d8dca5d4d2dd87"),
    # OBELiX (NRC/Mila), CC-BY 4.0.
    "obelix.csv": ("https://raw.githubusercontent.com/NRC-Mila/OBELiX/main/data/processed.csv",
                   "3402dfdfa8e1d75e68f42d87ebd24e6f"),
    # Borg et al., Sci. Data 7, 368 (2020), Apache 2.0.
    "mpea.csv": ("https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/master/MPEA_dataset.csv",
                 "6d29eb6018157b863ca0033ccec936d5"),
}


def main():
    DATA.mkdir(exist_ok=True)
    for name, (url, md5) in SOURCES.items():
        dest = DATA / name
        if not dest.exists():
            part = dest.with_suffix(".part")  # an interrupted download never looks complete
            urllib.request.urlretrieve(url, part)
            part.replace(dest)
        got = hashlib.md5(dest.read_bytes()).hexdigest()
        print(f"{name:<14} {dest.stat().st_size // 1024:>5} KB  " +
              ("ok" if got == md5 else f"WARNING: md5 {got} differs from {md5} - upstream changed; "
                                       "flag ids and published numbers will not match"))


if __name__ == "__main__":
    main()
