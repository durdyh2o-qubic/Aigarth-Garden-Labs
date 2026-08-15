"""Local tools the Grok bot can call against Garden Labs data and sims."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SIM_DIR = REPO_ROOT / "simulations"
RESULTS_DIR = REPO_ROOT / "results"
MINING_DIR = REPO_ROOT / "mining-logs"

# Ensure simulations/ is importable for short evolution runs
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _result_csv_paths() -> list[Path]:
    paths = list(SIM_DIR.glob("results_mut*.csv")) + list(RESULTS_DIR.glob("results_mut*.csv"))
    # Prefer simulations/ copies; de-dupe by name keeping newest mtime
    by_name: dict[str, Path] = {}
    for p in paths:
        prev = by_name.get(p.name)
        if prev is None or p.stat().st_mtime >= prev.stat().st_mtime:
            by_name[p.name] = p
    # Sort newest-first; when checkout mtimes collide, prefer later timestamp in filename
    return sorted(
        by_name.values(),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )


def list_simulation_runs(limit: int = 12) -> dict[str, Any]:
    """List recent simulation result CSVs with peak fitness."""
    rows = []
    for path in _result_csv_paths()[: max(1, min(limit, 50))]:
        try:
            df = pd.read_csv(path)
            peak = float(df["best_fitness"].max()) if "best_fitness" in df.columns else None
            gens = int(len(df))
            mut = float(df["mut"].iloc[0]) if "mut" in df.columns and len(df) else None
        except Exception as exc:  # noqa: BLE001 — surface parse errors to the model
            rows.append({"file": path.name, "error": str(exc)})
            continue
        rows.append(
            {
                "file": path.name,
                "path": str(path.relative_to(REPO_ROOT)),
                "generations": gens,
                "mut": mut,
                "peak_fitness": peak,
                "mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            }
        )
    return {"runs": rows, "count": len(rows)}


def summarize_fitness(file: str | None = None) -> dict[str, Any]:
    """Summarize one results CSV (defaults to newest)."""
    paths = _result_csv_paths()
    if not paths:
        return {"error": "No results_mut*.csv files found under simulations/ or results/."}

    if file:
        match = next((p for p in paths if p.name == file or str(p).endswith(file)), None)
        if match is None:
            return {"error": f"File not found: {file}", "available": [p.name for p in paths[:20]]}
        path = match
    else:
        path = paths[0]

    df = pd.read_csv(path)
    if "best_fitness" not in df.columns:
        return {"error": f"{path.name} missing best_fitness column", "columns": list(df.columns)}

    fitness = df["best_fitness"].astype(float)
    peak_idx = int(fitness.idxmax())
    return {
        "file": path.name,
        "path": str(path.relative_to(REPO_ROOT)),
        "generations": int(len(df)),
        "mut": float(df["mut"].iloc[0]) if "mut" in df.columns else None,
        "peak_fitness": float(fitness.max()),
        "peak_generation": int(df.loc[peak_idx, "gen"]) if "gen" in df.columns else peak_idx + 1,
        "final_fitness": float(fitness.iloc[-1]),
        "mean_fitness": float(fitness.mean()),
        "std_fitness": float(fitness.std(ddof=0)),
        "trend": "improving"
        if fitness.iloc[-1] > fitness.iloc[0]
        else "declining"
        if fitness.iloc[-1] < fitness.iloc[0]
        else "flat",
        "last_5": [
            {"gen": int(r["gen"]) if "gen" in df.columns else i + 1, "best_fitness": float(r["best_fitness"])}
            for i, (_, r) in enumerate(df.tail(5).iterrows())
        ],
    }


def parse_mining_log(path: str | None = None) -> dict[str, Any]:
    """Parse a Qubic mining log via mining-logs/parser.py helpers."""
    if str(MINING_DIR) not in sys.path:
        sys.path.insert(0, str(MINING_DIR))
    from parser import parse_qubic_log  # type: ignore  # local mining-logs module

    if path:
        target = Path(path)
        if not target.is_absolute():
            target = (REPO_ROOT / path).resolve()
    else:
        candidates = sorted(
            [p for p in MINING_DIR.iterdir() if p.suffix.lower() in {".txt", ".log", ".csv"}],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        # Prefer raw logs over any pre-parsed csv named parsed_results.csv for parser demo
        raw = [p for p in candidates if p.name != "parsed_results.csv"]
        if not raw:
            return {
                "error": "No mining log files found in mining-logs/.",
                "hint": "Drop a .txt/.log file into mining-logs/ then retry.",
            }
        target = raw[0]

    if not target.exists():
        return {"error": f"Mining log not found: {target}"}

    if target.suffix.lower() == ".csv":
        df = pd.read_csv(target)
    else:
        df = parse_qubic_log(str(target))

    if df is None or df.empty:
        return {"file": target.name, "entries": 0, "note": "Parser returned no rows."}

    summary: dict[str, Any] = {
        "file": target.name,
        "entries": int(len(df)),
        "columns": list(df.columns),
    }
    if "it_s" in df.columns:
        summary["it_s_mean"] = float(df["it_s"].mean())
        summary["it_s_max"] = float(df["it_s"].max())
    if "efficiency" in df.columns:
        summary["efficiency_mean"] = float(df["efficiency"].mean())
    if "seed" in df.columns:
        seeds = [s for s in df["seed"].dropna().unique().tolist() if s]
        summary["seeds"] = seeds[:10]
    if "epoch" in df.columns:
        summary["epochs"] = {
            "min": int(df["epoch"].min()),
            "max": int(df["epoch"].max()),
        }
    summary["tail"] = df.tail(5).to_dict(orient="records")
    return summary


def run_short_evolution(
    mut: float = 0.20,
    gens: int = 5,
    pop: int = 32,
    size: int = 512,
    seed: str | None = None,
) -> dict[str, Any]:
    """Run a short hyperidentity evolution (capped for interactive use)."""
    gens = max(1, min(int(gens), 20))
    pop = max(8, min(int(pop), 128))
    size = max(64, min(int(size), 512))
    mut = float(mut)

    from hyper_tissue import AigarthTissue

    if seed:
        s = int(seed, 16) % (2**32)
    else:
        s = 42

    tissue = AigarthTissue(size=size, seed=s)
    history = []
    best_child = None
    best_fit = float("-inf")

    for g in range(gens):
        pop_data = tissue.evolve_population(pop_size=pop, generations=1, mut_rate=mut)
        fit = float(pop_data[0][1])
        history.append({"gen": g + 1, "best_fitness": fit})
        if fit > best_fit:
            best_fit = fit
            best_child = pop_data[0][0]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = SIM_DIR / f"results_mut{mut}_grok_{ts}.csv"
    pd.DataFrame([{**h, "mut": mut} for h in history]).to_csv(out_csv, index=False)
    if best_child is not None:
        import numpy as np

        np.save(SIM_DIR / f"best_child_mut{mut}_grok_{ts}.npy", best_child)

    return {
        "mut": mut,
        "gens": gens,
        "pop": pop,
        "size": size,
        "seed_int": s,
        "peak_fitness": best_fit,
        "history": history,
        "results_csv": str(out_csv.relative_to(REPO_ROOT)),
    }


def lab_status() -> dict[str, Any]:
    """High-level snapshot of local garden artifacts."""
    runs = list_simulation_runs(limit=5)
    peaks = [r.get("peak_fitness") for r in runs["runs"] if isinstance(r.get("peak_fitness"), (int, float))]
    mining_files = [
        p.name
        for p in MINING_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".txt", ".log", ".csv"}
    ] if MINING_DIR.exists() else []
    return {
        "repo_root": str(REPO_ROOT),
        "recent_runs": runs["runs"],
        "best_local_peak": max(peaks) if peaks else None,
        "mining_log_files": mining_files,
        "simulation_modules": {
            "hyper_tissue": (SIM_DIR / "hyper_tissue.py").exists(),
            "run_experiment": (SIM_DIR / "run_experiment.py").exists(),
        },
    }


TOOL_HANDLERS = {
    "lab_status": lambda **_: lab_status(),
    "list_simulation_runs": lambda **kwargs: list_simulation_runs(**kwargs),
    "summarize_fitness": lambda **kwargs: summarize_fitness(**kwargs),
    "parse_mining_log": lambda **kwargs: parse_mining_log(**kwargs),
    "run_short_evolution": lambda **kwargs: run_short_evolution(**kwargs),
}


def tool_schemas() -> list[dict[str, Any]]:
    """JSON schemas for xAI function calling."""
    return [
        {
            "name": "lab_status",
            "description": "Snapshot of local Aigarth Garden artifacts: recent runs, peaks, mining logs present.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "list_simulation_runs",
            "description": "List recent results_mut*.csv simulation runs with peak fitness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max runs to list (1-50).",
                        "default": 12,
                    }
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "summarize_fitness",
            "description": "Summarize fitness curve for one results CSV (defaults to newest).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "description": "CSV filename, e.g. results_mut0.2_20260508_1944.csv",
                    }
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "parse_mining_log",
            "description": "Parse a Qubic mining log in mining-logs/ (or given path) and summarize it/s, seeds, epochs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Optional path relative to repo root or absolute path.",
                    }
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "run_short_evolution",
            "description": "Run a short Interactive Tissue evolution (capped: gens<=20, pop<=128) and save CSV under simulations/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mut": {"type": "number", "description": "Mutation rate", "default": 0.2},
                    "gens": {"type": "integer", "description": "Generations (max 20)", "default": 5},
                    "pop": {"type": "integer", "description": "Population size (max 128)", "default": 32},
                    "size": {"type": "integer", "description": "Tissue size (max 512)", "default": 512},
                    "seed": {
                        "type": "string",
                        "description": "Optional hex mining seed string",
                    },
                },
                "additionalProperties": False,
            },
        },
    ]


def execute_tool(name: str, arguments: dict[str, Any] | str | None = None) -> str:
    """Execute a tool and return JSON text for the model."""
    if isinstance(arguments, str):
        arguments = json.loads(arguments) if arguments.strip() else {}
    arguments = arguments or {}
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = handler(**arguments)
    except TypeError as exc:
        return json.dumps({"error": f"Bad arguments for {name}: {exc}"})
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"{name} failed: {exc}"})
    return json.dumps(result, default=str)
