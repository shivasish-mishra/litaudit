"""Download the three source databases into data/. Never commit data/ (Liverpool licence)."""
import pathlib
import urllib.request

DATA = pathlib.Path(__file__).parent / "data"

SOURCES = {
    # Hargreaves et al., npj Comput. Mater. 9, 9 (2023). Free for academic use; cite the University of Liverpool.
    "liverpool.csv": "http://pcwww.liv.ac.uk/~msd30/lmds/LiIonDatabase.csv",
    # OBELiX (NRC/Mila), CC-BY 4.0.
    "obelix.csv": "https://raw.githubusercontent.com/NRC-Mila/OBELiX/main/data/processed.csv",
    # Borg et al., Sci. Data 7, 368 (2020), Apache 2.0.
    "mpea.csv": "https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/master/MPEA_dataset.csv",
}


def main():
    DATA.mkdir(exist_ok=True)
    for name, url in SOURCES.items():
        dest = DATA / name
        if dest.exists():
            print(f"skip {name} (exists)")
            continue
        urllib.request.urlretrieve(url, dest)
        print(f"got  {name}  {dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
