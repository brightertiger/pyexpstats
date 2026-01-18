"""
Input validation utilities for expstats.

This module provides validation functions to ensure inputs are valid
before performing statistical calculations.
"""

import math
import warnings
from typing import Union, Optional, List


class SmallSampleWarning(UserWarning):
    """Warning raised when sample size is very small."""
    pass


def validate_finite(value: float, name: str = "value") -> float:
    """
    Validate that a value is finite (not NaN or infinity).

    Args:
        value: The value to validate
        name: Name of the parameter for error messages

    Returns:
        The validated value as a float

    Raises:
        TypeError: If value is not a number
        ValueError: If value is NaN or infinity
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if math.isnan(value):
        raise ValueError(f"{name} cannot be NaN")
    if math.isinf(value):
        raise ValueError(f"{name} cannot be infinity")
    return float(value)


def validate_rate(value: float, name: str = "rate") -> float:
    """
    Validate that a value is a valid rate/proportion between 0 and 1.

    Args:
        value: The rate to validate
        name: Name of the parameter for error messages

    Returns:
        The validated rate as a float

    Raises:
        TypeError: If value is not a number
        ValueError: If value is not between 0 and 1, or is NaN/infinity
    """
    value = validate_finite(value, name)
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")
    return value


def validate_positive(
    value: Union[int, float],
    name: str = "value",
    allow_zero: bool = False
) -> float:
    """
    Validate that a value is positive (or non-negative if allow_zero=True).

    Args:
        value: The value to validate
        name: Name of the parameter for error messages
        allow_zero: If True, zero is allowed

    Returns:
        The validated value as a float

    Raises:
        TypeError: If value is not a number
        ValueError: If value is not positive (or non-negative)
    """
    value = validate_finite(value, name)
    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} must be non-negative, got {value}")
    else:
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")
    return value


def validate_alpha(alpha: float) -> float:
    """
    Validate significance level (alpha).

    Args:
        alpha: Significance level (e.g., 0.05)

    Returns:
        The validated alpha as a float

    Raises:
        TypeError: If alpha is not a number
        ValueError: If alpha is not between 0 and 1 (exclusive)
    """
    alpha = validate_finite(alpha, "alpha")
    if alpha <= 0 or alpha >= 1:
        raise ValueError(f"alpha must be between 0 and 1 (exclusive), got {alpha}")
    return alpha


def validate_power(power: float) -> float:
    """
    Validate statistical power.

    Args:
        power: Statistical power (e.g., 0.80)

    Returns:
        The validated power as a float

    Raises:
        TypeError: If power is not a number
        ValueError: If power is not between 0 and 1 (exclusive)
    """
    power = validate_finite(power, "power")
    if power <= 0 or power >= 1:
        raise ValueError(f"power must be between 0 and 1 (exclusive), got {power}")
    return power


def validate_confidence(confidence: int, name: str = "confidence") -> int:
    """
    Validate confidence level (as percentage).

    Args:
        confidence: Confidence level as percentage (e.g., 95)
        name: Name of the parameter for error messages

    Returns:
        The validated confidence level as an integer

    Raises:
        TypeError: If confidence is not a number
        ValueError: If confidence is not between 50 and 99.99
    """
    if not isinstance(confidence, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(confidence).__name__}")
    if math.isnan(confidence) or math.isinf(confidence):
        raise ValueError(f"{name} cannot be NaN or infinity")
    if confidence < 50 or confidence >= 100:
        raise ValueError(
            f"{name} must be between 50 and 99.99 (percentage), got {confidence}. "
            f"Common values are 90, 95, or 99."
        )
    return int(confidence) if confidence == int(confidence) else confidence


def validate_sample_size(
    n: int,
    name: str = "sample_size",
    warn_if_small: bool = True,
    min_recommended: int = 30
) -> int:
    """
    Validate sample size.

    Args:
        n: Sample size to validate
        name: Name of the parameter for error messages
        warn_if_small: If True, warn when sample is below min_recommended
        min_recommended: Minimum recommended sample size (default 30)

    Returns:
        The validated sample size as an integer

    Raises:
        TypeError: If n is not a number
        ValueError: If n is not positive

    Warns:
        SmallSampleWarning: If n < min_recommended and warn_if_small=True
    """
    if not isinstance(n, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(n).__name__}")
    if math.isnan(n) or math.isinf(n):
        raise ValueError(f"{name} cannot be NaN or infinity")
    if n <= 0:
        raise ValueError(f"{name} must be positive, got {n}")

    n_int = int(n)

    if warn_if_small and n_int < min_recommended:
        warnings.warn(
            f"{name}={n_int} is below the recommended minimum of {min_recommended}. "
            f"Results may be unreliable with small samples.",
            SmallSampleWarning
        )

    return n_int


def validate_visitors(
    visitors: int,
    conversions: int,
    visitors_name: str = "visitors",
    conversions_name: str = "conversions"
) -> tuple:
    """
    Validate visitors and conversions for conversion analysis.

    Args:
        visitors: Number of visitors
        conversions: Number of conversions
        visitors_name: Name of visitors parameter for error messages
        conversions_name: Name of conversions parameter for error messages

    Returns:
        Tuple of (validated_visitors, validated_conversions)

    Raises:
        TypeError: If inputs are not numbers
        ValueError: If visitors <= 0, conversions < 0, or conversions > visitors
    """
    if not isinstance(visitors, (int, float)):
        raise TypeError(f"{visitors_name} must be a number, got {type(visitors).__name__}")
    if not isinstance(conversions, (int, float)):
        raise TypeError(f"{conversions_name} must be a number, got {type(conversions).__name__}")

    visitors = int(visitors)
    conversions = int(conversions)

    if visitors <= 0:
        raise ValueError(f"{visitors_name} must be positive, got {visitors}")
    if conversions < 0:
        raise ValueError(f"{conversions_name} cannot be negative, got {conversions}")
    if conversions > visitors:
        raise ValueError(
            f"{conversions_name} ({conversions}) cannot exceed {visitors_name} ({visitors})"
        )

    return visitors, conversions


def validate_sidedness(sidedness: str) -> str:
    """
    Validate test sidedness.

    Args:
        sidedness: Either "one-sided" or "two-sided"

    Returns:
        The validated sidedness string

    Raises:
        ValueError: If sidedness is not valid
    """
    valid = ["one-sided", "two-sided"]
    if sidedness not in valid:
        raise ValueError(f"sidedness must be one of {valid}, got {sidedness}")
    return sidedness


def validate_allocation_ratio(ratio: float) -> float:
    """
    Validate allocation ratio for experiments.

    Args:
        ratio: Allocation ratio (e.g., 1.0 for 50/50 split)

    Returns:
        The validated ratio as a float

    Raises:
        TypeError: If ratio is not a number
        ValueError: If ratio is not positive
    """
    ratio = validate_finite(ratio, "allocation_ratio")
    if ratio <= 0:
        raise ValueError(f"allocation_ratio must be positive, got {ratio}")
    return ratio


def validate_list_not_empty(lst: List, name: str = "list") -> List:
    """
    Validate that a list is not empty.

    Args:
        lst: The list to validate
        name: Name of the parameter for error messages

    Returns:
        The validated list

    Raises:
        TypeError: If input is not a list
        ValueError: If list is empty
    """
    if not isinstance(lst, (list, tuple)):
        raise TypeError(f"{name} must be a list or tuple, got {type(lst).__name__}")
    if len(lst) == 0:
        raise ValueError(f"{name} cannot be empty")
    return lst


def validate_same_length(*arrays, names: Optional[List[str]] = None) -> None:
    """
    Validate that multiple arrays have the same length.

    Args:
        *arrays: Arrays to compare
        names: Optional list of names for error messages

    Raises:
        ValueError: If arrays have different lengths
    """
    if len(arrays) < 2:
        return

    lengths = [len(arr) for arr in arrays]
    if len(set(lengths)) > 1:
        if names:
            details = ", ".join(f"{n}={l}" for n, l in zip(names, lengths))
        else:
            details = ", ".join(str(l) for l in lengths)
        raise ValueError(f"All arrays must have the same length. Got: {details}")


def validate_rate_or_percentage(value: float, name: str = "rate") -> float:
    """
    Validate a rate, accepting both decimal (0.05) and percentage (5) formats.

    Values > 1 are treated as percentages and converted to decimals.

    Args:
        value: The rate to validate (either as decimal or percentage)
        name: Name of the parameter for error messages

    Returns:
        The validated rate as a decimal float between 0 and 1

    Raises:
        TypeError: If value is not a number
        ValueError: If the converted rate is not valid

    Examples:
        validate_rate_or_percentage(0.05)  # Returns 0.05
        validate_rate_or_percentage(5)     # Returns 0.05
        validate_rate_or_percentage(150)   # Raises ValueError (150% > 100%)
    """
    value = validate_finite(value, name)

    # Convert percentage to decimal if > 1
    if value > 1:
        value = value / 100

    if value < 0 or value > 1:
        raise ValueError(
            f"{name} must be between 0 and 1 (or 0% and 100%), got {value}. "
            f"Use either decimal format (0.05) or percentage format (5)."
        )

    # Warn about edge cases
    if value == 0:
        warnings.warn(
            f"{name}=0 (0%) - this is an edge case that may cause issues in some calculations.",
            UserWarning
        )
    elif value == 1:
        warnings.warn(
            f"{name}=1 (100%) - this is an edge case that may cause issues in some calculations.",
            UserWarning
        )

    return value
