#!/usr/bin/env python
"""Run REPaL on data/cdr_1 through run_experiments.py, writing to results/cdr_run/.

A separate results folder keeps results/summary.* and results/aggregate.* unchanged.
usage: python tools/run_cdr.py --device-profile gpu
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run_experiments as r

r.DATASET_SPLITS["cdr"] = ["1"]
r.RESULTS_DIR = r.REPO_ROOT / "results" / "cdr_run"
sys.argv = [sys.argv[0], "--datasets", "cdr", "--data-root", "data", "--continue-on-error"] + sys.argv[1:]
r.main()
