#!/usr/bin/env python3
"""
Compare librelane PDK runs - area, sizing, timing (metrics + STA).
Highlights the better value between each pair of runs.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────

def add_comparison_row(table: Table, header: str, values: list[Any],
                       fmt: str = ".4f", unit: str = "",
                       lower_better: bool = True):
    """Add a row to a rich Table, coloring the best/worst numeric values."""
    formatted = []
    for v in values:
        if v is None:
            formatted.append("N/A")
        elif isinstance(v, float):
            formatted.append(f"{v:{fmt}}{unit}")
        elif isinstance(v, int):
            formatted.append(f"{v:,}{unit}")
        else:
            formatted.append(str(v) + unit)

    valid = [(i, v) for i, v in enumerate(values) if v is not None and isinstance(v, (int, float))]
    if len(valid) >= 2:
        if lower_better:
            best_idx = min(valid, key=lambda x: x[1])[0]
            worst_idx = max(valid, key=lambda x: x[1])[0]
        else:
            best_idx = max(valid, key=lambda x: x[1])[0]
            worst_idx = min(valid, key=lambda x: x[1])[0]

        cells = []
        for i, s in enumerate(formatted):
            if values[i] is None:
                cells.append(s)
            elif best_idx != worst_idx and i == best_idx:
                cells.append(f"[bold green]{s}[/bold green]")
            elif best_idx != worst_idx and i == worst_idx:
                cells.append(f"[bold red]{s}[/bold red]")
            else:
                cells.append(s)
    else:
        cells = formatted

    table.add_row(header, *cells)


def section_row(table: Table, title: str, ncols: int):
    """Insert a section-header row that spans the table."""
    table.add_row(f"[bold cyan underline]{title}[/]", *[""] * (ncols - 1))


# ── Parsers ───────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def parse_sta_summary(path: Path) -> dict:
    result = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        if "\u2502" not in line:
            continue
        parts = [p.strip() for p in line.split("\u2502") if p.strip() != ""]
        if not parts:
            continue
        corner = parts[0]
        if corner in ("", "Corner/Group", "Hold", "Worst", "Reg",
                       "Setup", "of which", "Slack", "Paths",
                       "TNS", "Count", "reg to", "reg"):
            continue
        try:
            result[corner] = {
                "hold_ws": float(parts[1]) if len(parts) > 1 and parts[1] not in ("N/A", "") else None,
                "hold_vio_count": int(parts[4]) if len(parts) > 4 and parts[4] not in ("N/A", "") else None,
                "setup_ws": float(parts[6]) if len(parts) > 6 and parts[6] not in ("N/A", "") else None,
                "setup_tns": float(parts[8]) if len(parts) > 8 and parts[8] not in ("N/A", "") else None,
                "setup_vio_count": int(parts[9]) if len(parts) > 9 and parts[9] not in ("N/A", "") else None,
                "max_slew_violations": int(parts[12]) if len(parts) > 12 and parts[12] not in ("N/A", "") else None,
            }
        except (ValueError, IndexError):
            continue
    return result


def parse_violator_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    result = []
    for line in path.read_text().splitlines():
        m = re.match(r"\[setup (.+?)\] (.+?) -> (.+?) : (.+)", line.strip())
        if m:
            result.append(f"{m.group(2)} -> {m.group(3)}: {m.group(4)}")
    return result


# ── Data collection ───────────────────────────────────────────────────────────

class RunData:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.resolved = load_json(path / "resolved.json")
        self.metrics = load_json(path / "final" / "metrics.json")
        self.sta_summary = parse_sta_summary(
            path / "55-openroad-stapostpnr" / "summary.rpt"
        )
        self.worst_violators = parse_violator_list(
            path / "55-openroad-stapostpnr" / "nom_ss_100C_1v60" / "violator_list.rpt"
        )

    @property
    def design_name(self) -> str:
        return self.resolved.get("DESIGN_NAME", "unknown")

    def m(self, key: str, default=None) -> Any:
        return self.metrics.get(key, default)


def discover_runs(base: Path) -> list[RunData]:
    runs = []
    for entry in sorted(base.iterdir()):
        if (entry.is_dir()
                and entry.name.startswith("RUN_")
                and (entry / "resolved.json").exists()):
            runs.append(RunData(entry))
    return runs


# ── Table builders ────────────────────────────────────────────────────────────

def make_table(labels: list[str], title: str = "") -> Table:
    t = Table(
        title=title,
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold cyan",
        header_style="bold",
        expand=False,
    )
    t.add_column("Metric", style="dim", no_wrap=True)
    for label in labels:
        t.add_column(label, justify="right")
    return t


def build_config_table(runs: list[RunData], labels: list[str]) -> Table:
    n = len(labels) + 1
    t = make_table(labels, title="Design Configuration")
    add_comparison_row(t, "Design Name", [r.design_name for r in runs], lower_better=False)
    add_comparison_row(t, "Clock Period (ns)", [r.resolved.get("CLOCK_PERIOD") for r in runs], ".0f")
    add_comparison_row(t, "Synthesis Strategy", [r.resolved.get("SYNTH_STRATEGY") for r in runs], lower_better=False)
    add_comparison_row(t, "Std Cell Library", [r.resolved.get("STD_CELL_LIBRARY") for r in runs], lower_better=False)
    return t


def build_area_table(runs: list[RunData], labels: list[str]) -> Table:
    n = len(labels) + 1
    t = make_table(labels, title="Core Area")

    section_row(t, "Die / Core", n)
    add_comparison_row(t, "Die Area (um\u00b2)", [r.m("design__die__area", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Core Area (um\u00b2)", [r.m("design__core__area", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Die BBox", [r.m("design__die__bbox", "?") for r in runs], lower_better=False)
    add_comparison_row(t, "Core BBox", [r.m("design__core__bbox", "?") for r in runs], lower_better=False)

    section_row(t, "Utilization", n)
    add_comparison_row(t, "Instance Area (um\u00b2)", [r.m("design__instance__area", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Std Cell Area (um\u00b2)", [r.m("design__instance__area__stdcell", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Utilization",
                       [round(r.m("design__instance__utilization", 0) * 100, 2) for r in runs],
                       ",.2f", "%", lower_better=False)
    return t


def build_sizing_table(runs: list[RunData], labels: list[str]) -> Table:
    n = len(labels) + 1
    t = make_table(labels, title="Sizing Information")

    section_row(t, "Cell Counts", n)
    add_comparison_row(t, "Total Instances", [r.m("design__instance__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Std Cell Instances", [r.m("design__instance__count__stdcell", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Fill Cells", [r.m("design__instance__count__class:fill_cell", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Tap Cells", [r.m("design__instance__count__class:tap_cell", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Timing Repair Buffers", [r.m("design__instance__count__class:timing_repair_buffer", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Setup Buffers", [r.m("design__instance__count__setup_buffer", 0) for r in runs], ",.0f", lower_better=True)

    section_row(t, "Cell Areas", n)
    add_comparison_row(t, "Inverter Area (um\u00b2)", [r.m("design__instance__area__class:inverter", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Multi-Input Comb Area", [r.m("design__instance__area__class:multi_input_combinational_cell", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Fill Cell Area", [r.m("design__instance__area__class:fill_cell", 0) for r in runs], ",.1f", lower_better=True)
    add_comparison_row(t, "Tap Cell Area", [r.m("design__instance__area__class:tap_cell", 0) for r in runs], ",.1f", lower_better=True)

    section_row(t, "Routing", n)
    add_comparison_row(t, "Route Wirelength", [r.m("route__wirelength", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Route Vias", [r.m("route__vias", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "DRC Errors", [r.m("route__drc_errors", 0) for r in runs], ",.0f", lower_better=True)
    return t


def build_timing_table(runs: list[RunData], labels: list[str]) -> Table:
    n = len(labels) + 1
    t = make_table(labels, title="Timing (Overall Worst-Case)")

    section_row(t, "Setup", n)
    add_comparison_row(t, "Setup WNS (ns)", [r.m("timing__setup__wns", 0) for r in runs], ".4f", lower_better=False)
    add_comparison_row(t, "Setup TNS (ns)", [r.m("timing__setup__tns", 0) for r in runs], ".4f", lower_better=False)
    add_comparison_row(t, "Setup Vios", [r.m("timing__setup_vio__count", 0) for r in runs], ",.0f", lower_better=True)

    section_row(t, "Hold", n)
    add_comparison_row(t, "Hold WNS (ns)", [r.m("timing__hold__wns", 0) for r in runs], ".4f", lower_better=False)
    add_comparison_row(t, "Hold TNS (ns)", [r.m("timing__hold__tns", 0) for r in runs], ".4f", lower_better=False)
    add_comparison_row(t, "Hold Vios", [r.m("timing__hold_vio__count", 0) for r in runs], ",.0f", lower_better=True)

    section_row(t, "DRV", n)
    add_comparison_row(t, "Max Slew Violations", [r.m("design__max_slew_violation__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Max Fanout Violations", [r.m("design__max_fanout_violation__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Max Cap Violations", [r.m("design__max_cap_violation__count", 0) for r in runs], ",.0f", lower_better=True)
    return t


def build_power_table(runs: list[RunData], labels: list[str]) -> Table:
    n = len(labels) + 1
    t = make_table(labels, title="Power & IR Drop")

    section_row(t, "Power", n)
    add_comparison_row(t, "Total Power (mW)", [r.m("power__total", 0) * 1000 for r in runs], ",.3f", lower_better=True)
    add_comparison_row(t, "Internal (mW)", [r.m("power__internal__total", 0) * 1000 for r in runs], ",.3f", lower_better=True)
    add_comparison_row(t, "Switching (mW)", [r.m("power__switching__total", 0) * 1000 for r in runs], ",.3f", lower_better=True)
    add_comparison_row(t, "Leakage (uW)", [r.m("power__leakage__total", 0) * 1e6 for r in runs], ",.3f", lower_better=True)

    section_row(t, "IR Drop", n)
    add_comparison_row(t, "IR Drop Avg (V)", [r.m("ir__drop__avg", 0) for r in runs], ".4f", lower_better=True)
    add_comparison_row(t, "IR Drop Worst (V)", [r.m("ir__drop__worst", 0) for r in runs], ".4f", lower_better=True)
    return t


def build_signoff_table(runs: list[RunData], labels: list[str]) -> Table:
    t = make_table(labels, title="Signoff Checks")

    add_comparison_row(t, "Magic DRC Errors", [r.m("magic__drc_error__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "KLayout DRC Errors", [r.m("klayout__drc_error__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "LVS Errors", [r.m("design__lvs_error__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "XOR Differences", [r.m("design__xor_difference__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Power Grid Violations", [r.m("design__power_grid_violation__count", 0) for r in runs], ",.0f", lower_better=True)
    add_comparison_row(t, "Disconnected Pins", [r.m("design__disconnected_pin__count", 0) for r in runs], ",.0f", lower_better=True)
    return t


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    runs_dir = Path(__file__).parent / "runs"
    runs = discover_runs(runs_dir)

    if not runs:
        console.print("[bold red]No runs found in ./runs/[/bold red]")
        sys.exit(1)
    if len(runs) < 2:
        console.print(f"[bold red]Only {len(runs)} run(s) found \u2014 need at least 2 to compare.[/bold red]")
        sys.exit(1)

    labels = [f"{r.design_name}  {r.name.removeprefix('RUN_')}" for r in runs]

    console.print()
    console.print(build_config_table(runs, labels))
    console.print()
    console.print(build_area_table(runs, labels))
    console.print()
    console.print(build_sizing_table(runs, labels))
    console.print()
    console.print(build_timing_table(runs, labels))
    console.print()
    console.print(build_power_table(runs, labels))
    console.print()
    console.print(build_signoff_table(runs, labels))
    console.print()

    console.print(Panel("[bold cyan]Worst Setup Violators (nom_ss corner)[/bold cyan]", box=box.DOUBLE))
    console.print()
    for i, r in enumerate(runs):
        console.print(f"  [bold]{labels[i]}[/bold]")
        if r.worst_violators:
            for v in r.worst_violators:
                console.print(f"    {v}")
        else:
            console.print("    [bold green]No setup violations[/bold green]")
        console.print()


if __name__ == "__main__":
    main()
