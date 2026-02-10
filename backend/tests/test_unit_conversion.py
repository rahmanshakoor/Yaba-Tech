"""Tests for unit conversion service."""

import pytest

from src.services.unit_conversion import batch_convert, convert_units


def test_same_unit_conversion():
    """Test converting between same units returns original value."""
    assert convert_units(5.0, "kg", "kg") == 5.0
    assert convert_units(3.0, "liter", "liter") == 3.0


def test_mass_conversions():
    """Test mass unit conversions."""
    # kg to g
    result = convert_units(1.0, "kg", "g")
    assert abs(result - 1000.0) < 0.01

    # lb to kg
    result = convert_units(1.0, "lb", "kg")
    assert abs(result - 0.453592) < 0.001

    # oz to kg
    result = convert_units(16.0, "oz", "kg")
    assert abs(result - 0.453592) < 0.01


def test_volume_conversions():
    """Test volume unit conversions."""
    # liter to ml
    result = convert_units(1.0, "liter", "ml")
    assert abs(result - 1000.0) < 0.01

    # gallon to liter
    result = convert_units(1.0, "gallon", "liter")
    assert abs(result - 3.78541) < 0.001


def test_package_conversions():
    """Test package-to-base-unit conversions."""
    result = convert_units(2.0, "case", "kg")
    assert result == 20.0

    result = convert_units(1.0, "bag", "kg")
    assert result == 5.0


def test_custom_factor():
    """Test conversion with custom factor."""
    result = convert_units(3.0, "case", "kg", custom_factor=12.5)
    assert result == 37.5


def test_invalid_conversion():
    """Test that incompatible unit conversion raises ValueError."""
    with pytest.raises(ValueError, match="Cannot convert"):
        convert_units(1.0, "kg", "liter")


def test_batch_convert():
    """Test batch conversion of multiple values."""
    values = [1.0, 2.0, 3.0]
    result = batch_convert(values, "lb", "kg")
    assert len(result) == 3
    assert abs(result[0] - 0.453592) < 0.001
    assert abs(result[1] - 0.907184) < 0.001


def test_batch_convert_custom_factor():
    """Test batch conversion with custom factor."""
    values = [1.0, 2.0, 5.0]
    result = batch_convert(values, "case", "kg", custom_factor=10.0)
    assert result == [10.0, 20.0, 50.0]


def test_case_insensitive():
    """Test that unit conversion is case-insensitive."""
    result = convert_units(1.0, "KG", "G")
    assert abs(result - 1000.0) < 0.01


def test_whitespace_handling():
    """Test that whitespace in unit names is handled."""
    result = convert_units(1.0, " kg ", " g ")
    assert abs(result - 1000.0) < 0.01
