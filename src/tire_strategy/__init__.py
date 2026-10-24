"""Latent Tire Degradation & Undercut Strategy Engine.

Estimates tire-age-related pace change from F1 timing data (via FastF1)
and simulates undercut outcomes under explicit, documented assumptions.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tire-strategy")
except PackageNotFoundError:  # running from source without `pip install -e .`
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]