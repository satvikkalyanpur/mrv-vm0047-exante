"""Run the scenario and write every output. Usage: python run.py"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mrv import figures, pipeline


def main():
    result = pipeline.run()
    extra = pipeline.write_outputs(result)
    out = os.path.join(pipeline.ROOT, "outputs")
    for name, draw in (
        ("figure_credits_over_time.png", lambda: figures.credits_over_time(result)),
        ("figure_waterfall.png", lambda: figures.waterfall(result)),
        ("figure_sensitivity.png", lambda: figures.sensitivity_ranges(
            extra["sensitivity"], result.summary["credits_issuable"])),
        ("figure_parcel.png", lambda: figures.parcel_map(
            pipeline._path(result.scenario["site"]["parcel_geojson"]), result.summary["area_ha"])),
        ("figure_progress_so_far.png", lambda: figures.progress_so_far(
            extra["progress"], result.summary["as_of"])),
        ("figure_reality_check.png", lambda: figures.reality_check(result, extra["reality_check"])),
    ):
        ax = draw()
        ax.figure.tight_layout()
        ax.figure.savefig(os.path.join(out, name), dpi=200)
        plt.close(ax.figure)

    s, ill, crop = result.summary, extra["illustrative"].summary, extra["cropland"]
    print(f"{s['scenario']}")
    print(f"{s['methodology']}, {s['approach']} approach: {result.approach_reason}")
    print(f"Carbon stored by year {s['horizon_years']}:   {s['stock_change_tco2e']:.1f} t CO2e")
    print(f"Credits issuable (reference): {s['credits_issuable']:.1f}  "
          f"({s['credits_per_ha_per_year']:.2f} per ha per year)")
    print(f"Credits issuable (illustrative deductions): {ill['credits_issuable']:.1f}")
    print(f"As of {s['as_of']} ({s['years_elapsed']:.2f} years in): "
          f"{s['credits_accrued_to_date']:.1f} accrued, {s['credits_issued_to_date']:.0f} issued")
    model, das10 = extra["reality_check"].iloc[0], extra["reality_check"].iloc[1]
    print(f"Reality check: model {model.carbon_kg_per_palm:.1f} kg C per palm at year 10; "
          f"measured stands {extra['reality_check'].carbon_kg_per_palm[1:5].min():.1f}-"
          f"{extra['reality_check'].carbon_kg_per_palm[1:5].max():.1f} kg C per palm")
    print(f"If planted on working cropland: {crop['new_land_ha']:.2f} ha of new land elsewhere; "
          f"leakage cancels all removals above {crop['breakeven_carbon_stock_tc_per_ha']:.0f} t C/ha on that land")
    print(f"Ledger head: {extra['ledger'][-1]['hash'][:16]}...  outputs written to {out}")


if __name__ == "__main__":
    main()
