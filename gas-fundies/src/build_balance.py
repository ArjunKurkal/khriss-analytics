"""Build the US monthly natural gas balance (Bcf/d) — Gas Fundies core.

Identity (net view):
    supply = dry production + pipeline imports + LNG imports
    demand = consumption + pipeline exports + LNG exports
    supply - demand = implied change in storage

The implied change is compared with the REPORTED change in working gas
(from weekly storage stocks, month-end to month-end). The difference is
the balancing item and is published as its own line — EIA's own monthly
balance carries a balancing item of the same construction, and hiding it
would make the table look more precise than the data are.

Gross view (for the dashboard's EIA-style table) is derived in
build_dashboard_data.py: withdrawals join supply, injections join demand.

Inputs (curated Parquet, from the pullers):
    monthly_us_balance_inputs.parquet   period, component, value_mmcf
    monthly_state_production.parquet    period, state, marketed_production_mmcf
    storage_weekly.parquet              week_ending, region, working_gas_bcf
    config/regions.json                 state -> production region

Outputs:
    balance_monthly.parquet   one row per month, all lines in Bcf/d,
                              plus storage changes in Bcf and Bcf/d
    production_by_region.parquet  period, region, dry_production_bcfd
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data    # noqa: E402
from khriss_data.io import read_parquet, write_parquet  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
FACTOR = json.loads((HERE / "config" / "regions.json").read_text())[
    "lng_feedgas_fuel_factor"]["value"]

SECTORS = ["consumption_residential_us", "consumption_commercial_us",
           "consumption_industrial_us", "consumption_electric_power_us"]
OTHER_CONS = ["consumption_lease_fuel_us", "consumption_pipeline_fuel_us",
              "consumption_vehicle_fuel_us"]


def main() -> None:
    _, curated = project_data("gas-fundies")

    inputs = read_parquet(curated / "monthly_us_balance_inputs.parquet")
    wide = inputs.pivot_table(index="period", columns="component",
                              values="value_mmcf", aggfunc="sum")
    wide.index = pd.to_datetime(wide.index)
    days = wide.index.days_in_month
    bcfd = wide.div(1000.0).div(days, axis=0)  # MMcf/month -> Bcf/d

    out = pd.DataFrame(index=bcfd.index)
    out["dry_production"] = bcfd["dry_production_us"]
    out["imports_pipeline"] = bcfd["imports_pipeline_us"]
    out["imports_lng"] = bcfd["imports_lng_us"]
    out["total_supply"] = out[["dry_production", "imports_pipeline",
                               "imports_lng"]].sum(axis=1)

    out["residential"] = bcfd["consumption_residential_us"]
    out["commercial"] = bcfd["consumption_commercial_us"]
    out["industrial"] = bcfd["consumption_industrial_us"]
    out["power_burn"] = bcfd["consumption_electric_power_us"]
    present_other = [c for c in OTHER_CONS if c in bcfd.columns]
    out["other_consumption"] = bcfd[present_other].sum(axis=1)
    out["consumption_total_reported"] = bcfd["consumption_total_us"]
    # Sector check: res+com+ind+power+other should track the reported
    # total; any gap is kept visible rather than forced.
    out["consumption_sector_gap"] = (
        out["consumption_total_reported"]
        - out[["residential", "commercial", "industrial", "power_burn",
               "other_consumption"]].sum(axis=1))
    out["exports_pipeline"] = bcfd["exports_pipeline_us"]
    out["exports_lng"] = bcfd["exports_lng_us"]
    out["lng_feedgas_estimate"] = out["exports_lng"] * FACTOR  # memo line
    out["total_demand"] = (out["consumption_total_reported"]
                           + out["exports_pipeline"] + out["exports_lng"])
    out["supply_minus_demand"] = out["total_supply"] - out["total_demand"]

    # Reported storage change from weekly stocks (month-end levels).
    storage = read_parquet(curated / "storage_weekly.parquet")
    total_label = [r for r in storage["region"].unique()
                   if "lower 48" in str(r).lower() or str(r).lower() == "total"]
    if total_label:
        s = storage[storage["region"] == total_label[0]].copy()
        s["week_ending"] = pd.to_datetime(s["week_ending"])
        month_end = (s.set_index("week_ending")["working_gas_bcf"]
                     .resample("ME").last().dropna())
        # Align to the balance's month-START index (the resample gives
        # month-end stamps; without this the reindex matches nothing).
        month_end.index = month_end.index.to_period("M").to_timestamp()
        reported_bcf = month_end.diff()
        out["storage_change_reported_bcf"] = reported_bcf.reindex(out.index)
        out["storage_change_reported_bcfd"] = (
            out["storage_change_reported_bcf"] / days)
        out["implied_storage_change_bcf"] = out["supply_minus_demand"] * days
        out["balancing_item_bcf"] = (out["storage_change_reported_bcf"]
                                     - out["implied_storage_change_bcf"])
        out["balancing_item_bcfd"] = out["balancing_item_bcf"] / days
    else:
        print("WARNING: no Lower 48 total in storage_weekly — "
              "storage reconciliation skipped, labels were: "
              f"{sorted(storage['region'].unique())}")

    out = out.reset_index().rename(columns={"period": "month"})
    write_parquet(out, curated / "balance_monthly.parquet", "balance_monthly")

    # Production by region (state detail stays in the source table).
    # EIA publishes dry production only for the US; states are marketed
    # production. Regional dry is an ESTIMATE: regional marketed scaled
    # by the month's US dry/marketed ratio. Both lines are written.
    regions = json.loads((HERE / "config" / "regions.json").read_text())
    state_to_region = {st: reg for reg, states in
                       regions["production_regions"].items() for st in states}
    prod = read_parquet(curated / "monthly_state_production.parquet")
    prod["period"] = pd.to_datetime(prod["period"])
    prod["region"] = prod["state"].map(state_to_region)
    unmapped = sorted(prod.loc[prod["region"].isna(), "state"].unique())
    if unmapped:
        print(f"WARNING: states with no production region: {unmapped}")
    prod = prod.dropna(subset=["region"])
    reg = (prod.groupby(["period", "region"])["marketed_production_mmcf"]
           .sum().reset_index())
    ratio = (wide["dry_production_us"] / wide["marketed_production_us"])
    reg["dry_production_est_mmcf"] = (
        reg["marketed_production_mmcf"]
        * reg["period"].map(ratio))
    dim = reg["period"].dt.days_in_month
    reg["marketed_production_bcfd"] = reg["marketed_production_mmcf"] / 1000.0 / dim
    reg["dry_production_bcfd"] = reg["dry_production_est_mmcf"] / 1000.0 / dim
    write_parquet(reg.rename(columns={"period": "month"}),
                  curated / "production_by_region.parquet",
                  "production_by_region")
    print(f"balance months: {out['month'].min()} to {out['month'].max()}")


if __name__ == "__main__":
    main()
