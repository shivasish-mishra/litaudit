"""Write-up figure: figures/litaudit.png (2x2 panels) + figures/panel_a..d.png for the video.
Run after fetch_data.py."""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from audit import AGREE, _arrhenius_series, arrhenius, planted_benchmark, run
from loaders import load_all

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
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


def panel_cross_db(ax, checks):
    x = checks[(checks.check == "cross_db")]
    lo, hi = -11, -1
    t = np.linspace(lo, hi, 2)
    ax.fill_between(t, t - AGREE, t + AGREE, color=GRID, alpha=0.7, lw=0)
    ax.plot(t, t, color=INK2, lw=1)
    for f, lab in [(1, "×10"), (2, "×100"), (3, "×1000")]:
        for s in (1, -1):
            ax.plot(t, t + s * f, color=INK2, lw=0.7, ls=(0, (3, 3)))
        ax.text(hi - 0.1, hi - f - 0.25, lab, color=INK2, fontsize=8, ha="right")
    scatter(ax, np.log10(x.reference.values), np.log10(x.value.values), x.diagnosis.values)
    notes = {"Nd0.25Li0.25TaO3": ("Nd-Li tantalate: S/m stored\nas S/cm (verified)", (-10.7, -4.6)),
             "Li6.5La3Zr1.75Te0.25O12": ("Te-LLZO: ~9× low vs\nthe paper (verified)", (-4.6, -7.6)),
             "Li3PS4": ("Li₃PS₄: β vs γ phase\n(not an error)", (-9.6, -2.6))}
    done = set()
    for _, r in x[x.composition.str.strip().isin(notes)].iterrows():
        k = r.composition.strip()
        if k in done:
            continue
        done.add(k)
        text, pos = notes[k]
        ax.annotate(text, (np.log10(r.reference), np.log10(r.value)), xytext=pos,
                    fontsize=7.5, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.set_xlim(lo, hi), ax.set_ylim(lo, hi)
    style(ax, "A  Same paper, two databases", "log₁₀ σ in OBELiX (S/cm)", "log₁₀ σ in Liverpool (S/cm)")
    ax.legend(loc="lower right", fontsize=8, frameon=False, labelcolor=INK2)


def panel_tabor(ax, checks):
    tab = checks[checks.check == "relation_tabor"]
    scatter(ax, tab.reference.values, tab.value.values, tab.diagnosis.values)
    hv = np.logspace(np.log10(80), np.log10(900), 2)
    c = 10 ** np.median(np.log10(tab.value / (tab.reference * 9.807 / 3)))
    band = tab.agree.iloc[0]
    ax.plot(hv, c * hv * 9.807 / 3, color=INK2, lw=1)
    ax.fill_between(hv, c * hv * 9.807 / 3 / 10 ** band, c * hv * 9.807 / 3 * 10 ** band, color=GRID, alpha=0.7, lw=0)
    r = tab[tab.doi == "10.1063/1.2734517"].iloc[0]
    ax.annotate("AlCoCrFeNiTi₀.₅: HV not in the\ncited paper (verified)", (r.reference, r.value),
                xytext=(r.reference * 1.25, r.value * 1.6), fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.set_xscale("log"), ax.set_yscale("log")
    style(ax, "B  Physics relation: YS ≈ c·HV·g/3", "Vickers hardness (HV)", "yield strength (MPa)")


def panel_arrhenius(ax, df, checks):
    """Method illustration on real data: the longest fully consistent Arrhenius series, with a x100 error planted
    in one interior point, re-checked. (Real Arrhenius flags are unverified, so none is showcased.)"""
    entries = df.assign(key=df.db + ":" + df.row_id + ":" + df.property).set_index("key")
    series = entries.db + "|" + entries.doi + "|" + entries.comp_key + "|" + entries.condition
    a = checks[checks.check == "arrhenius"].assign(series=lambda c: c.key_a.map(series))
    ok = a.groupby("series").diagnosis.apply(lambda d: (d == "agree").all())
    best = a[a.series.isin(ok[ok].index)].series.value_counts().idxmax()  # longest fully consistent series
    g = df.loc[series.reindex(df.db + ":" + df.row_id + ":" + df.property).values == best].sort_values("T_K")
    db, doi, prop = g.db.iloc[0], g.doi.iloc[0], g.property.iloc[0]
    bad = g.index[len(g) // 2]
    g = g.copy()
    g.loc[bad, "value"] *= 100
    planted = df.copy()  # plant into the full data so the check's noise band is the real one
    planted.loc[bad, "value"] *= 100
    res = arrhenius(planted)
    r = res[res.key_a == f"{db}:{g.loc[bad, 'row_id']}:{prop}"].iloc[0]
    entry = g.loc[bad]
    row_id = entry.row_id
    x, y = _arrhenius_series(g)
    ok = g.row_id.values != row_id
    ax.plot(x[ok][np.argsort(x[ok])], y[ok][np.argsort(x[ok])], color=INK2, lw=1, zorder=1)
    ax.scatter(x[ok], y[ok], s=26, c=STYLE["agree"][0], marker="o", edgecolors="white", linewidths=1, zorder=2,
               label="same paper, other temperatures")
    xb = 1000 / entry.T_K
    yb, ye = np.log10(entry.value * entry.T_K), np.log10(r.reference * entry.T_K)
    ax.scatter([xb], [ye], s=40, facecolors="none", edgecolors=INK2, linewidths=1.2, zorder=3, label="expected from neighbours")
    ax.scatter([xb], [yb], s=46, c=STYLE["named"][0], marker="s", edgecolors="white", linewidths=1, zorder=4,
               label="value with a planted ×100 slip")
    ax.annotate("", (xb, yb), (xb, ye), arrowprops=dict(arrowstyle="->", color=INK2, lw=0.8))
    ax.text(xb + 0.03, (yb + ye) / 2, f"{r.resid:+.2f} dex\n→ {r.diagnosis}", fontsize=7.5, color=INK, va="center")
    style(ax, f"D  Arrhenius check (planted error in a real series)", "1000/T (1/K)", "log₁₀ σT (S K/cm)")
    ax.text(0.98, 0.97, f"{entry.composition.strip()}\n{len(g)} temperatures, {doi}", transform=ax.transAxes,
            ha="right", va="top", fontsize=7, color=INK2)
    ax.legend(loc="lower left", fontsize=7.5, frameon=False, labelcolor=INK2)
    return r


def panel_benchmark(ax, bench):
    labels = [f.replace("sigma*T", "σT") for f in bench.factor]
    y = np.arange(len(bench))[::-1]
    ax.barh(y, bench.flagged, color=GRID, height=0.62, label="flagged")
    ax.barh(y, bench.named, color=STYLE["named"][0], height=0.36, label="cause named correctly")
    for yi, f, n in zip(y, bench.flagged, bench.named):
        ax.text(f + 0.02, yi, f"{n:.0%} / {f:.0%}", va="center", fontsize=7.5, color=INK)
    ax.set_yticks(y, labels, fontsize=7.5)
    ax.set_xlim(0, 1.3)
    ax.set_ylim(-0.6, len(bench) + 0.4)  # a free band above the bars for the legend
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    style(ax, "C  Planted errors, whole audit re-run", "share of corrupted entries (named / flagged)", "")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper right", ncol=2, fontsize=7.5, frameon=False, labelcolor=INK2)


def main():
    df = load_all()
    checks = run(df)
    bench = planted_benchmark(df)
    out = pathlib.Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10), layout="constrained")
    panel_cross_db(axes[0, 0], checks)
    panel_tabor(axes[0, 1], checks)
    panel_benchmark(axes[1, 0], bench)
    picked = panel_arrhenius(axes[1, 1], df, checks)
    fig.savefig(out / "litaudit.png", dpi=180, facecolor=SURF)
    fig.canvas.draw()
    for ax, name in zip(axes.flat, "abcd"):  # single panels, used by the video
        box = ax.get_tightbbox().transformed(fig.dpi_scale_trans.inverted()).padded(0.1)
        fig.savefig(out / f"panel_{name}.png", dpi=200, facecolor=SURF, bbox_inches=box)
    bench.to_csv(out / "benchmark.csv", index=False)
    print("wrote", out / "litaudit.png", "+ panel_a..d.png + benchmark.csv; panel D:", picked.composition, picked.doi)


if __name__ == "__main__":
    main()
