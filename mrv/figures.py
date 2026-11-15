"""Charts for the scenario report."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

TEAL, ORANGE, INK, MUTE, GRID = "#12908E", "#D9722A", "#2B3A42", "#6B7680", "#E3E7EA"

LABELS = {
    "equation": "Biomass equation",
    "performance_benchmark": "Performance benchmark",
    "uncertainty": "Uncertainty deduction",
    "buffer_rating": "Buffer rating",
    "survival_fraction": "Palm survival",
}
VALUE_NAMES = {"prayogo2018": "Prayogo 2018", "das2021_m2": "Das 2021 (height)", "das2021_m3": "Das 2021 (D²H)"}


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTE, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def credits_over_time(result, ax=None):
    s, sm = result.schedule, result.summary
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.8))
    _style(ax)
    out_of_range = s[s.height_within_equation_range == False]  # noqa: E712
    if len(out_of_range) and len(out_of_range) < len(s):
        ax.axvspan(0, out_of_range.year.max() + 0.5, color="#F3F5F6", zorder=0)
        ax.text(5.2, s.stock_change_tco2e.max() * 0.03,
                "shaded: palms below the equation's height range",
                fontsize=8, color=MUTE, va="bottom", ha="left")
    ax.plot(s.year, s.stock_change_tco2e, color=MUTE, lw=1.5, ls="--", label="Carbon stored (before deductions)")
    ax.plot(s.year, s.credits_accrued_cumulative, color=TEAL, lw=2.4, label="Credits accrued (after deductions)")
    ax.step(s.year, s.credits_issued_cumulative, where="post", color=ORANGE, lw=2.4, label="Credits issued at verification")
    for row in s[s.credits_issued_at_verification > 0].itertuples():
        ax.plot(row.year, row.credits_issued_cumulative, "o", color=ORANGE, ms=6, zorder=5)
        ax.annotate(f"{row.credits_issued_cumulative:.1f}", (row.year, row.credits_issued_cumulative),
                    textcoords="offset points", xytext=(-10, 12), ha="right", fontsize=9, color=ORANGE, fontweight="bold")
    t = sm["years_elapsed"]
    if 0 < t < s.year.max():
        ax.axvline(t, color=INK, lw=1, ls=":")
        ax.text(t + 0.12, s.stock_change_tco2e.max() * 0.62,
                f"{sm['as_of']}\n{sm['credits_accrued_to_date']:.1f} accrued\n{sm['credits_issued_to_date']:.0f} issued",
                fontsize=8.5, color=INK, va="top")
    ax.set_xticks(s.year)
    ax.set_xticklabels([f"{y}\n{c}" if y % 5 == 0 else str(y) for y, c in zip(s.year, s.calendar_year)])
    ax.set_xlabel("Years since planting", color=MUTE, fontsize=9)
    ax.set_ylabel("t CO₂e on the 1.27 ha parcel", color=MUTE, fontsize=9)
    ax.set_title("Credits over ten years, new-planting what-if (VM0047, reference case)",
                 loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0.2, 0.98))
    return ax


def waterfall(result, ax=None):
    sm = result.summary
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.4))
    _style(ax)
    gross = sm["stock_change_tco2e"]
    bench = gross * sm["performance_benchmark"]
    unc = (gross - bench) * sm["uncertainty_deducted"]
    steps = [
        ("Carbon stored", gross, None),
        ("Performance\nbenchmark", -bench,
             f"{sm['performance_benchmark']:.0%}" + (" (assumed)" if sm["performance_benchmark"] == 0 else "")),
        ("Uncertainty", -unc, f"{sm['uncertainty_deducted']:.0%}"),
        ("Leakage", -sm["leakage_tco2e"], "fallow land"),
        ("Buffer", -sm["buffer_tco2e"], f"{sm['buffer_fraction']:.0%}"),
        ("Credits\nissuable", sm["credits_issuable"], None),
    ]
    level = 0.0
    for i, (name, value, note) in enumerate(steps):
        total = i in (0, len(steps) - 1)
        bottom = 0.0 if total else level + min(value, 0)
        height = value if total else abs(value)
        color = TEAL if total else ORANGE
        ax.bar(i, height, bottom=bottom, color=color, width=0.62)
        label = f"{value:.1f}" if total else (f"−{abs(value):.1f}" if value else "0")
        ax.text(i, bottom + height + gross * 0.02, label, ha="center", fontsize=10, color=INK, fontweight="bold")
        if note:
            ax.text(i, bottom + height + gross * 0.085, note, ha="center", fontsize=8, color=MUTE)
        if not total:
            level += value
        else:
            level = value if i == 0 else level
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], fontsize=9, color=INK)
    ax.set_ylim(0, gross * 1.2)
    ax.set_ylabel("t CO₂e over ten years", color=MUTE, fontsize=9)
    ax.set_title("From carbon stored to credits issuable, year 10 (reference case)",
                 loc="left", fontsize=11, color=INK, fontweight="bold")
    return ax


def sensitivity_ranges(sens: pd.DataFrame, reference: float, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.2))
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    groups = []
    for key, g in sens.groupby("input", sort=False):
        lo, hi = g.loc[g.credits_issuable.idxmin()], g.loc[g.credits_issuable.idxmax()]
        groups.append((key, lo, hi))
    groups.sort(key=lambda x: x[2].credits_issuable - x[1].credits_issuable)

    def fmt(key, v):
        if key == "equation":
            return VALUE_NAMES.get(v, v)
        if key == "buffer_rating":
            return f"{float(v):.0f}%"
        return f"{float(v):.0%}"

    for i, (key, lo, hi) in enumerate(groups):
        ax.barh(i, hi.credits_issuable - lo.credits_issuable, left=lo.credits_issuable, color=TEAL, height=0.5)
        ax.text(lo.credits_issuable - 1.2, i, fmt(key, lo.value), ha="right", va="center", fontsize=8.5, color=MUTE)
        ax.text(hi.credits_issuable + 1.2, i, fmt(key, hi.value), ha="left", va="center", fontsize=8.5, color=MUTE)
    ax.axvline(reference, color=INK, lw=1, ls="--")
    ax.text(reference, len(groups) - 0.35, f"reference {reference:.1f}", ha="center", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([LABELS.get(k, k) for k, _, _ in groups], fontsize=9.5, color=INK)
    lo_all, hi_all = sens.credits_issuable.min(), sens.credits_issuable.max()
    ax.set_xlim(lo_all - (hi_all - lo_all) * 0.22, hi_all + (hi_all - lo_all) * 0.22)
    ax.set_ylim(-0.6, len(groups) - 0.1)
    ax.set_xlabel("Credits issuable over ten years (t CO₂e)", color=MUTE, fontsize=9)
    ax.set_title("What moves the answer most: one input changed at a time",
                 loc="left", fontsize=11, color=INK, fontweight="bold")
    return ax


def parcel_map(geojson_path: str, area_ha: float, ax=None):
    """The parcel boundary drawn to scale, with side lengths."""
    import json
    import math
    with open(geojson_path, encoding="utf-8") as f:
        ring = json.load(f)["features"][0]["geometry"]["coordinates"][0]
    lat0 = sum(p[1] for p in ring[:-1]) / (len(ring) - 1)
    lon0 = sum(p[0] for p in ring[:-1]) / (len(ring) - 1)
    a, e2, phi = 6378137.0, 0.00669437999, math.radians(lat0)
    my = math.radians(1) * a * (1 - e2) / (1 - e2 * math.sin(phi) ** 2) ** 1.5
    mx = math.radians(1) * a * math.cos(phi) / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    pts = [((p[0] - lon0) * mx, (p[1] - lat0) * my) for p in ring]
    if ax is None:
        _, ax = plt.subplots(figsize=(6.4, 5.6))
    xs, ys = zip(*pts)
    ax.fill(xs, ys, color=TEAL, alpha=0.18, zorder=1)
    ax.plot(xs, ys, color=TEAL, lw=2.2, zorder=2)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        length = math.hypot(x2 - x1, y2 - y1)
        mxp, myp = (x1 + x2) / 2, (y1 + y2) / 2
        norm = math.hypot(mxp, myp) or 1
        ax.text(mxp + 9 * mxp / norm, myp + 9 * myp / norm, f"{length:.0f} m", ha="center", va="center",
                fontsize=9, color=INK)
    ax.text(0, 4, f"{area_ha:.2f} ha", ha="center", va="center", fontsize=15, color=INK, fontweight="bold")
    ax.text(0, -9, f"{lat0:.5f}° N, {lon0:.5f}° E", ha="center", va="center", fontsize=8.5, color=MUTE)
    x_min, y_min, y_max = min(xs), min(ys), max(ys)
    ax.plot([x_min, x_min + 50], [y_min - 22, y_min - 22], color=INK, lw=2)
    ax.text(x_min + 25, y_min - 28, "50 m", ha="center", va="top", fontsize=8.5, color=INK)
    x_max = max(xs)
    ax.annotate("", xy=(x_max + 14, y_max + 4), xytext=(x_max + 14, y_max - 22),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
    ax.text(x_max + 14, y_max + 8, "N", ha="center", va="bottom", fontsize=10, color=INK, fontweight="bold")
    ax.set_aspect("equal")
    ax.set_xlim(x_min - 26, x_max + 30)
    ax.set_ylim(y_min - 40, y_max + 24)
    ax.axis("off")
    ax.set_title("Study parcel, Chikkamagaluru (Malnad), Karnataka", loc="left", fontsize=11,
                 color=INK, fontweight="bold")
    return ax


def progress_so_far(progress: pd.DataFrame, as_of: str, ax=None):
    """Credits accrued month by month since planting."""
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.2))
    _style(ax)
    ax.bar(progress.month, progress.credits_accrued, color=TEAL, width=0.7)
    marks = sorted(set([3, 6, 12, int(progress.month.max())]) & set(progress.month))
    for m in marks:
        row = progress[progress.month == m].iloc[0]
        ax.text(m + 0.38, row.credits_accrued + progress.credits_accrued.max() * 0.03,
                f"{row.credits_accrued:.2f} accrued\npalms {row.mean_height_m:.2f} m", ha="right", va="bottom",
                fontsize=8.5, color=INK)
    ax.set_xticks(progress.month)
    ax.set_xticklabels([d[:7] if i % 3 == 0 else "" for i, d in enumerate(progress.date)], fontsize=8.5)
    ax.set_ylim(0, progress.credits_accrued.max() * 1.3)
    ax.set_xlabel("Month (planting = first bar)", color=MUTE, fontsize=9)
    ax.set_ylabel("Credits accrued, t CO₂e", color=MUTE, fontsize=9)
    ax.set_title(f"So far: {int(progress.month.max())} months since planting, modelled. Issued to date: 0",
                 loc="left", fontsize=11, color=INK, fontweight="bold")
    return ax


def reality_check(result, check: pd.DataFrame, ax=None):
    """Modelled carbon per palm against palms in stands that were measured."""
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.4))
    _style(ax)
    s, k, sm = result.schedule, result.rules["constants"], result.summary
    per_palm = s.stock_change_tco2e / k["co2_per_c"] / sm["area_ha"] * 1000 / sm["palms_per_ha"]
    ax.plot(s.year, per_palm, color=TEAL, lw=2.4, label="This model")
    ax.annotate(f"{per_palm.iloc[-1]:.1f}", (s.year.iloc[-1], per_palm.iloc[-1]), textcoords="offset points",
                xytext=(-8, 6), ha="right", fontsize=9, color=TEAL, fontweight="bold")
    das = check[check.source.str.startswith("Das")]
    ax.scatter(das.age_years, das.carbon_kg_per_palm, color=ORANGE, s=55, zorder=5,
               label="Measured stands, Assam, above + below ground (Das et al. 2021)")
    for row in das.itertuples():
        ax.annotate(f"{row.carbon_kg_per_palm:.1f}", (row.age_years, row.carbon_kg_per_palm),
                    textcoords="offset points", xytext=(8, -3), fontsize=8.5, color=MUTE)
    bh = check[check.source.str.startswith("Bhoomika")]
    ax.scatter(bh.age_years, bh.carbon_kg_per_palm, facecolors="white", edgecolors=INK, s=55, zorder=5,
               label="Malnad trial, authors' estimate, above ground only (Bhoomika et al. 2023)")
    for row in bh.itertuples():
        ax.annotate(f"{row.carbon_kg_per_palm:.1f}", (row.age_years, row.carbon_kg_per_palm),
                    textcoords="offset points", xytext=(8, -3), fontsize=8.5, color=MUTE)
    ax.set_xlabel("Stand age, years", color=MUTE, fontsize=9)
    ax.set_ylabel("Carbon per palm, kg C", color=MUTE, fontsize=9)
    ax.set_xlim(0, 37)
    ax.set_ylim(0, 14.5)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Reality check: modelled carbon per palm against measured stands",
                 loc="left", fontsize=11, color=INK, fontweight="bold")
    return ax


def observed_record(obs: dict, planting_date: str | None = None, end_date: str | None = None, ax=None):
    """Monthly rainfall with any NDVI series on a second axis."""
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4.2))
    _style(ax)
    weather = obs.get("weather")
    if weather is not None and len(weather):
        months = pd.to_datetime(weather.month)
        ax.bar(months, weather.rain_mm, width=22, color="#9CC9D8", label="Rainfall, mm per month (NASA POWER)")
        ax.set_ylabel("Rainfall, mm per month", color=MUTE, fontsize=9)
    else:
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
    ax2 = ax.twinx()
    for side in ("top", "left", "bottom"):
        ax2.spines[side].set_visible(False)
    ax2.spines["right"].set_color(GRID)
    ax2.tick_params(colors=MUTE, labelsize=9)
    for key, label, color in (("ndvi_modis", "NDVI, MODIS 250 m pixel", TEAL),
                              ("ndvi_sentinel2", "NDVI, Sentinel-2 10 m parcel mean", ORANGE)):
        df = obs.get(key)
        if df is not None and len(df):
            df = df.dropna(subset=["ndvi"])
            ax2.plot(pd.to_datetime(df.date), df.ndvi, color=color, lw=1.8, marker="o", ms=3, label=label)
    poc = obs.get("ndvi_poc")
    if poc is not None and len(poc):
        row = poc.iloc[0]
        ax2.plot([pd.Timestamp(row.period_start), pd.Timestamp(row.period_end)], [row.ndvi, row.ndvi],
                 color=INK, lw=3, solid_capstyle="butt", label=f"NDVI {row.ndvi:.3f}, Sentinel-2, proof of concept")
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("NDVI", color=MUTE, fontsize=9)
    if planting_date:
        ax.axvline(pd.Timestamp(planting_date), color=INK, lw=1, ls=":")
        ax2.text(pd.Timestamp(planting_date), 0.97, " planting (what-if)", fontsize=8.5, color=INK, va="top")
    if end_date:
        starts = [pd.Timestamp(planting_date)] if planting_date else []
        if poc is not None and len(poc):
            starts.append(pd.Timestamp(poc.iloc[0].period_start))
        if starts:
            ax.set_xlim(min(starts) - pd.Timedelta(days=15), pd.Timestamp(end_date) + pd.Timedelta(days=15))
    handles = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax2.legend(handles, labels, frameon=False, fontsize=8.5, loc="lower left")
    ax.set_title("Observed at the plot: rainfall and greenness", loc="left", fontsize=11, color=INK, fontweight="bold")
    return ax
