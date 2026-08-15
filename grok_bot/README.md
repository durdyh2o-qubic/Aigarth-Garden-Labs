# Grok Bot — Aigarth Garden Labs

Truth-seeking research assistant powered by the **xAI Grok API**, with local tools over this repo’s hyperidentity simulations and mining logs.

## Setup

```bash
# from repo root
source garden_venv/bin/activate
pip install -r grok_bot/requirements.txt
export XAI_API_KEY=xai-...   # https://console.x.ai/
```

Optional model override:

```bash
export GROK_MODEL=grok-4.6
```

## Usage

```bash
# interactive chat
python -m grok_bot

# one-shot
python -m grok_bot -q "Summarize the best local fitness run and suggest a next experiment."

# local snapshot only (no API key)
python -m grok_bot --status
```

## Tools Grok can call

| Tool | Purpose |
|------|---------|
| `lab_status` | Recent runs, local peak fitness, mining-log files present |
| `list_simulation_runs` | List `results_mut*.csv` with peaks |
| `summarize_fitness` | Peak / trend / last-5 for one CSV |
| `parse_mining_log` | Parse Qubic trainer logs via `mining-logs/parser.py` |
| `run_short_evolution` | Capped Interactive Tissue run (gens≤20, pop≤128) |

## Notes

- Active garden research lives in [Aigarth-Garden-Labs-2](https://github.com/durdyh2o-qubic/Aigarth-Garden-Labs-2); this bot works against the archived sim artifacts here and can be copied forward.
- Short evolution runs write new `results_mut*_grok_*.csv` (and `.npy`) under `simulations/`.
