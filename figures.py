"""Write-up figure: figures/litaudit.png (3 panels). Run after fetch_data.py."""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from audit import AGREE, cross_db, planted_benchmark, relations
from loaders import load_all

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# marker + colour per diagnosis class, so identity never relies on colour alone
STYLE = {"agree": ("#a8a7a0", "o", "consistent"),
         "named": ("#2a78d6", "s", "known unit/quantity factor"),
         "unexplained": ("#eb6834", "^", "unexplained")}


def cls(d):
    return d if d in ("agree", "unexplained") else "named"


def scatter(ax, x, y, diag):
    for k, (c, m, lab) in STYLE.items():
        sel = np.array([cls(d) == k for d in diag])
        ax.scatter(x[sel], y[sel], s=36 if k != "agree" else 22, c=c, marker=m, label=lab,
                   edgecolors="white", linewidths=1, zorder=3 if k != "agree" else 2)


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.set_xlabel(xlabel, color=INK2)
    ax.set_ylabel(ylabel, color=INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(color=GRID, linewidth=0.6)
    for s in ax.spines.values():
        s.set_visible(False)


def main():
    df = load_all()
    xdb, rel = cross_db(df), relations(df)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), layout="constrained",
                             gridspec_kw={"width_ratios": [1.15, 1.15, 1]})

    # A: two conductivity databases, factor bands
    ax = axes[0]
    lo, hi = -11, -1
    t = np.linspace(lo, hi, 2)
    ax.fill_between(t, t - AGREE, t + AGREE, color=GRID, alpha=0.7, lw=0)
    ax.plot(t, t, color=INK2, lw=1)
    for f, lab in [(1, "×10"), (2, "×100"), (3, "×1000")]:
        for s in (1, -1):
            ax.plot(t, t + s * f, color=INK2, lw=0.7, ls=(0, (3, 3)))
        ax.text(hi - 0.1, hi - f - 0.25, lab, color=INK2, fontsize=8, ha="right")
    scatter(ax, np.log10(xdb.reference.values), np.log10(xdb.value.values), xdb.diagnosis.values)
    # label text position (x, y) in axis data units, chosen to avoid the points and legend
    notes = {"Nd0.25Li0.25TaO3": ("Nd-Li tantalate: S/m stored\nas S/cm (verified)", (-10.7, -4.6)),
             "Li6.5La3Zr1.75Te0.25O12": ("Te-LLZO: 7–9× low\n(verified)", (-4.6, -7.6)),
             "Li3PS4": ("Li₃PS₄: β vs γ phase\n(not an error)", (-9.6, -2.6))}
    done = set()
    for _, r in xdb[xdb.composition.isin(notes)].iterrows():
        if r.composition in done:
            continue
        done.add(r.composition)
        text, pos = notes[r.composition]
        ax.annotate(text, (np.log10(r.reference), np.log10(r.value)), xytext=pos,
                    fontsize=7.5, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.set_xlim(lo, hi), ax.set_ylim(lo, hi)
    style(ax, "A  Same paper, two databases", "log₁₀ σ in OBELiX (S/cm)", "log₁₀ σ in Liverpool (S/cm)")
    ax.legend(loc="lower right", fontsize=8, frameon=False, labelcolor=INK2)

    # B: hardness vs yield strength (MPEA)
    ax = axes[1]
    tab = rel[rel.check == "relation_tabor"]
    scatter(ax, tab.reference.values, tab.value.values, tab.diagnosis.values)
    hv = np.logspace(np.log10(80), np.log10(900), 2)
    c = 10 ** np.median(np.log10(tab.value / (tab.reference * 9.807 / 3)))
    ax.plot(hv, c * hv * 9.807 / 3, color=INK2, lw=1)
    ax.fill_between(hv, c * hv * 9.807 / 3 / 10**AGREE, c * hv * 9.807 / 3 * 10**AGREE, color=GRID, alpha=0.7, lw=0)
    r = tab[tab.doi == "10.1063/1.2734517"].iloc[0]
    ax.annotate("AlCoCrFeNiTi₀.₅: HV not in the\ncited paper (verified)", (r.reference, r.value),
                xytext=(r.reference * 1.25, r.value * 1.6), fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.set_xscale("log"), ax.set_yscale("log")
    style(ax, "B  Physics relation: YS ≈ c·HV·g/3", "Vickers hardness (HV)", "yield strength (MPa)")

    # C: planted-error benchmark (single series, no legend)
    ax = axes[2]
    bench = planted_benchmark(pd_concat(xdb, rel))
    labels = [f"{p.replace('ionic_conductivity', 'σ').replace('_vs_', ' vs ').replace('density_exp', 'density')}: {f}"
              for p, f in zip(bench.property, bench.factor)]
    y = np.arange(len(bench))[::-1]
    ax.barh(y, bench.recall, color=STYLE["named"][0], height=0.6)
    for yi, v in zip(y, bench.recall):
        ax.text(v + 0.02, yi, f"{v:.0%}", va="center", fontsize=8, color=INK)
    ax.set_yticks(y, labels, fontsize=7.5)
    ax.set_xlim(0, 1.15)
    style(ax, "C  Planted errors correctly named", "fraction recovered (all were flagged)", "")
    ax.grid(axis="y", visible=False)

    out = pathlib.Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out / "litaudit.png", dpi=200, facecolor="#fcfcfb")
    fig.canvas.draw()
    for ax, name in zip(axes, "abc"):  # single panels, used by the video
        box = ax.get_tightbbox().transformed(fig.dpi_scale_trans.inverted()).padded(0.1)
        fig.savefig(out / f"panel_{name}.png", dpi=200, facecolor="#fcfcfb", bbox_inches=box)
    print("wrote", out / "litaudit.png", "+ panel_a/b/c.png")


def pd_concat(*frames):
    import pandas as pd
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    main()
