# Progress log

Decisions, findings and open questions, newest milestone last.
Each finding states its evidence and date, so it can be rechecked.

## Milestone 1: Scope and environment

### Environment (checked 2026-10-23)
- Windows 11, Python 3.13.14 (Microsoft Store build), project venv at `.venv`
- 15.4 GB RAM, ~390 GB free disk
- GPUs: Intel Arc (integrated), NVIDIA RTX 3050 Laptop 6 GB. Not used so far; tabular models are expected to run fine on CPU. To be measured, not assumed, in Milestone 5.

### Decisions
- **src layout package** (`src/tire_strategy/`) installed with `pip install -e ".[dev]"`, so scripts, notebooks and tests share one implementation and packaging errors surface early.
- **Config file** `configs/data.yaml` holds session selection and load options; it will be saved alongside results for traceability.
- **First sample:** 2023 and 2024 Bahrain GP races. Same circuit across two seasons gives a natural race-grouped train/test split later.
- **FastF1 >= 3.9** (installed 3.9.0): uses `Cache.configure()`; `enable_cache()` is deprecated in 3.9.
- **Raw data stays local:** `data/*` is git-ignored; FastF1's cache at `data/raw/fastf1_cache/` is the immutable raw layer.

### Finding: FastF1 historical data now requires an F1 account login (2026-10-24)
- Unauthenticated requests to `https://livetiming.formula1.com/static/...` returned **HTTP 401**, including the five per-session files for the 2023 Bahrain race (SessionInfo, TimingData, TimingAppData, TrackStatus, WeatherData).
- FastF1's authentication docs still state that historical data needs no login; observed behaviour contradicts this.
- Signing in with a **free formula1.com account** (no F1TV subscription) was sufficient: the 2023 Bahrain race downloaded (7.9 MB cache) with FastF1 3.9.0.
- Considered alternative: OpenF1 (`api.openf1.org`, free, 2023+, CC BY-NC-SA 4.0). Kept as a fallback if FastF1 access changes again.

### Credentials
- Entered at FastF1's interactive prompt only. Never stored in the repo, `.env`, config or code.
- FastF1 stores a reusable token outside the project (`%LOCALAPPDATA%\fastf1\f1auth_token.json`). Cached sessions need no login.
- Reproducing the dataset requires a free F1 account; to be stated in the README.

### First look: 2023 Bahrain GP race (`scripts/check_fastf1_access.py`)
- 20 drivers, 1,056 lap rows, 57 laps; 31 lap columns, 161 weather rows, 73 race-control messages.
- `LapStartDate` is 100% missing. Laps and weather share session-relative time (`LapStartTime`, `Time`); race-control messages use wall-clock time and must be linked by `Lap`.
- `PitInTime`/`PitOutTime` are present only on in/out laps (absence means no pit event, not missing data).
- Candidate exclusion flags: `TrackStatus`, `IsAccurate`, `Deleted`, `FastF1Generated`.

### Second look: 2024 Bahrain GP race (2026-10-24)
- Loaded with the stored login token (no prompt). 20 drivers, 1,129 lap rows, 57 laps; 157 weather rows, 69 race-control messages. Cache for both races: 17.0 MB.
- Same 31 lap columns as 2023. `LapStartDate` again 100% missing, so this is systematic, not a one-off.
- **dtypes depend on missingness:** `IsPersonalBest` is `bool` in 2024 but `object` in 2023 (one missing value). The loader must set dtypes explicitly rather than trust inference.
- `PitInTime`/`PitOutTime` present on 43 laps each; `SpeedFL` missing on exactly 43 laps (2023: 53 missing vs 52 in-laps). Supports the hypothesis that pit-lane laps skip the finish-line speed trap; to verify row by row.
- `Sector1Time` missing on 21 laps in both races, consistent with lap 1 for 20 drivers plus one other lap; to verify.

### Open questions for Milestone 2
- Why are 84 driver-laps absent (retirements, lapped cars)?
- Are `Sector1Time` gaps exactly lap 1? Are `SpeedFL` gaps exactly the pit in-laps?
- Why are only 11 driver-laps absent in 2024 vs 84 in 2023?
- Does `Compound` contain placeholder values? Does `TyreLife` start above 1 for used sets?
- Decode `TrackStatus` codes into explicit labels.

### Remaining Milestone 1 steps
- [x] Confirm cache reuse: second run faster and needed no login prompt (2026-10-24)
- [x] Load 2024 Bahrain race (`--index 1`) and compare columns/missingness (2026-10-24)
- [ ] Add `.gitattributes` to normalise line endings
- [ ] Remove `scripts/test.py` (superseded by `check_fastf1_access.py`)
