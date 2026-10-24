
import fastf1
import pandas as pd

# Enable local caching (recommended)
fastf1.Cache.enable_cache("./configs/")

# Select the 2024 British Grand Prix race
session = fastf1.get_session(2024, "British Grand Prix", "R")

# Download and load session data
session.load()

# Access all drivers' lap data
laps = session.laps

# Inspect the dataset
print(laps.head())
print(laps.columns.tolist())