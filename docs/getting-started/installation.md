# Installation

## Requirements

- Python 3.9 or higher
- pip (Python package manager)

## Install from PyPI

The easiest way to install pyexpstats is via pip:

```bash
pip install pyexpstats
```

## Install from Source

To install the latest development version from source:

```bash
git clone https://github.com/pyexpstats/pyexpstats.git
cd pyexpstats
pip install -e .
```

## Dependencies

pyexpstats automatically installs the following dependencies:

| Package | Purpose |
|---------|---------|
| `numpy` | Numerical computations |
| `scipy` | Statistical functions |
| `pydantic` | Data validation |

For the web interface, additional dependencies are installed:

| Package | Purpose |
|---------|---------|
| `fastapi` | Web API framework |
| `uvicorn` | ASGI server |

## Verify Installation

After installation, verify that pyexpstats is working:

```python
from pyexpstats import conversion, magnitude

# Calculate sample size for a conversion test
plan = conversion.sample_size(current_rate=5, lift_percent=10)
print(f"Sample size needed: {plan.visitors_per_variant:,} per variant")
```

## Running the Web Interface

To start the web interface:

```bash
pyexpstats-server
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Troubleshooting

### Import Error

If you get an import error, make sure you have the correct Python version:

```bash
python --version  # Should be 3.9+
```

### Missing Dependencies

If dependencies are missing, reinstall with:

```bash
pip install --upgrade pyexpstats
```
