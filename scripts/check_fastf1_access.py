"""Smoke test: load one FastF1 session from configs/data.yaml and report what it contains.

This is a Milestone 1 check of environment, network access and caching.
It does not clean, filter or save any processed data.

Usage (from anywhere):
    python scripts/check_fastf1_access.py               # first session in the config
    python scripts/check_fastf1_access.py --index 1     # second session
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import fastf1
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "data.yaml"

logger = logging.getLogger("check_fastf1_access")


def load_config(path: Path) -> dict[str, Any]:
    """Read the YAML data config into a dict."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def describe_frame(name: str, df: pd.DataFrame) -> None:
    """Print shape, then each column's dtype and missing-value count."""
    print(f"\n=== {name}: {df.shape[0]} rows x {df.shape[1]} columns ===")
    summary = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "n_missing": df.isna().sum(),
        "pct_missing": (df.isna().mean() * 100).round(1),
    })
    print(summary.to_string())


def folder_size_mb(path: Path) -> float:
    """Total size of all files under `path`, in megabytes."""
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) / 1e6


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--index", type=int, default=0,
                        help="Which entry of `sessions` in the config to load (default: 0).")
    args = parser.parse_args()

    # Configure only this script's logger: FastF1 already has its own log handler,
    # and logging.basicConfig() would print every FastF1 message twice.
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    cfg = load_config(CONFIG_PATH)
    session_cfg = cfg["sessions"][args.index]

    # 1. Cache: resolve relative to the repo root (not the current folder) and create it,
    #    because FastF1 refuses a cache directory that does not exist.
    cache_dir = REPO_ROOT / cfg["fastf1"]["cache_dir"]
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.configure(cache_dir=str(cache_dir))
    logger.info("FastF1 %s, cache at %s", fastf1.__version__, cache_dir)

    # 2. Cheap lookup first: identify the event and check it before downloading anything.
    session = fastf1.get_session(session_cfg["season"], session_cfg["round"], session_cfg["session"])
    event_name = session.event["EventName"]
    if event_name != session_cfg["expected_event_name"]:
        raise ValueError(
            f"Config expects {session_cfg['expected_event_name']!r} for season "
            f"{session_cfg['season']} round {session_cfg['round']}, but FastF1 returned {event_name!r}."
        )
    logger.info("Matched %s %s, session %s (%s)", session_cfg["season"], event_name,
                session.name, session.date)

    # 3. Expensive step: download (or read from cache) and parse.
    session.load(**cfg["fastf1"]["load"])

    # 4. Report what we actually received. No cleaning or filtering here.
    #    FastF1 logs download failures as warnings instead of raising, so the first
    #    real signal of a failed download is that the laps were never loaded.
    try:
        laps = session.laps
    except fastf1.exceptions.DataNotLoadedError as err:
        raise RuntimeError(
            "Lap data did not load. Check the FastF1 warnings above (network, rate limit, "
            "or the session not existing in the timing archive)."
        ) from err
    print(f"\nDrivers: {laps['Driver'].nunique()}  |  Laps: {len(laps)}  |  "
          f"Max LapNumber: {laps['LapNumber'].max()}")
    describe_frame("session.laps", laps)
    if cfg["fastf1"]["load"].get("weather"):
        describe_frame("session.weather_data", session.weather_data)
    if cfg["fastf1"]["load"].get("messages"):
        describe_frame("session.race_control_messages", session.race_control_messages)

    print(f"\nCache folder size: {folder_size_mb(cache_dir):.1f} MB")


if __name__ == "__main__":
    main()