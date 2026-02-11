from pyexpstats import effects
from pyexpstats.effects import outcome
from pyexpstats.effects.outcome import conversion
from pyexpstats.effects.outcome import magnitude
from pyexpstats.effects.outcome import timing

# New modules
from pyexpstats import methods
from pyexpstats import diagnostics
from pyexpstats import planning
from pyexpstats import business
from pyexpstats import segments

__version__ = "0.2.0"

__all__ = [
    # Core effects
    "effects",
    "outcome",
    "conversion",
    "magnitude",
    "timing",
    # Testing methods
    "methods",
    # Diagnostics
    "diagnostics",
    # Planning
    "planning",
    # Business impact
    "business",
    # Segments
    "segments",
]
