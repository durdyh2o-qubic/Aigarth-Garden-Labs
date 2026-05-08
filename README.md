# Aigarth-Garden-Labs

**Living Experimental Observatory for Qubic Aigarth Hyperidentity Evolution (May 2026)**

Public garden laboratory studying the growth of the **Intelligent Tissue** through Useful Proof-of-Work, local ternary hyperidentity simulations, and Grok agentic workflows.

## Current Status (May 2026)
- ~60+ epochs into Aigarth Phase 2
- **Best fitness achieved**: **0.003989** (Mut=0.20 with Helix + Teacher-of-Teachers scoring)
- Sweet spot mutation: **≈ 0.20**
- Seed under study: `86F3893EDF74789F73BC2FAB0C80C6B5772FBD90257741EE942F03BE50D3C04B`

**Mission**: Truth-seeking documentation of decentralized AGI progress.

## Quick Start
```bash
cd simulations
source garden_venv/bin/activate
python run_experiment.py --mut 0.20 --gens 60 --pop 128 --seed 86F3893EDF74789F73BC2FAB0C80C6B5772FBD90257741EE942F03BE50D3C04B

```bash
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
garden_venv/
*.npy
*.csv
*.png
