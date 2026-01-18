from expstats import effects
from expstats.effects import outcome
from expstats.effects.outcome import conversion
from expstats.effects.outcome import magnitude
from expstats.effects.outcome import timing

# New modules
from expstats import methods
from expstats import diagnostics
from expstats import planning
from expstats import business
from expstats import segments

__version__ = "0.1.0"

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
