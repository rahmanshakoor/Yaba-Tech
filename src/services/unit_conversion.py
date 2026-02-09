"""Unit conversion utility using NumPy for converting supplier units to internal base units."""

import numpy as np

# Conversion factors to base units (kg for mass, liter for volume)
MASS_CONVERSIONS: dict[str, float] = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.453592,
    "oz": 0.0283495,
    "ton": 1000.0,
}

VOLUME_CONVERSIONS: dict[str, float] = {
    "liter": 1.0,
    "l": 1.0,
    "ml": 0.001,
    "gallon": 3.78541,
    "cup": 0.236588,
    "fl_oz": 0.0295735,
}

# Custom packaging conversions (configurable per item)
PACKAGE_CONVERSIONS: dict[str, dict[str, float]] = {
    "case": {"kg": 10.0, "liter": 12.0},  # default case sizes
    "bag": {"kg": 5.0},
    "box": {"kg": 2.5},
    "bottle": {"liter": 0.75},
    "can": {"liter": 0.33},
}


def convert_units(
    value: float,
    from_unit: str,
    to_unit: str,
    custom_factor: float | None = None,
) -> float:
    """Convert a value from one unit to another.

    Args:
        value: The quantity to convert.
        from_unit: Source unit (e.g., 'lb', 'case').
        to_unit: Target unit (e.g., 'kg', 'liter').
        custom_factor: Optional custom conversion factor (units of to_unit per 1 from_unit).

    Returns:
        Converted value in target units.

    Raises:
        ValueError: If conversion is not possible.
    """
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()

    if from_unit == to_unit:
        return float(value)

    if custom_factor is not None:
        return float(np.multiply(value, custom_factor))

    # Check mass conversions
    if from_unit in MASS_CONVERSIONS and to_unit in MASS_CONVERSIONS:
        base_value = np.multiply(value, MASS_CONVERSIONS[from_unit])
        return float(np.divide(base_value, MASS_CONVERSIONS[to_unit]))

    # Check volume conversions
    if from_unit in VOLUME_CONVERSIONS and to_unit in VOLUME_CONVERSIONS:
        base_value = np.multiply(value, VOLUME_CONVERSIONS[from_unit])
        return float(np.divide(base_value, VOLUME_CONVERSIONS[to_unit]))

    # Check package conversions
    if from_unit in PACKAGE_CONVERSIONS:
        pkg = PACKAGE_CONVERSIONS[from_unit]
        if to_unit in pkg:
            return float(np.multiply(value, pkg[to_unit]))

    raise ValueError(
        f"Cannot convert from '{from_unit}' to '{to_unit}'. "
        "Provide a custom_factor or add the conversion mapping."
    )


def batch_convert(
    values: list[float],
    from_unit: str,
    to_unit: str,
    custom_factor: float | None = None,
) -> list[float]:
    """Convert a list of values from one unit to another using NumPy vectorization.

    Args:
        values: List of quantities to convert.
        from_unit: Source unit.
        to_unit: Target unit.
        custom_factor: Optional custom conversion factor.

    Returns:
        List of converted values.
    """
    arr = np.array(values, dtype=np.float64)

    if custom_factor is not None:
        factor = custom_factor
    else:
        # Derive factor from single conversion
        factor = convert_units(1.0, from_unit, to_unit)

    result = np.multiply(arr, factor)
    return result.tolist()
