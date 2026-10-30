"""Unit-aware :class:`Parameter` value type.

Provides a dataclass storing a value with optional units and a
description, backed by pint for unit conversion, comparison, and
arithmetic operations that respect units.
"""
from dataclasses import dataclass, field, fields

from pint import UnitRegistry

UREG = UnitRegistry()


@dataclass
class Parameter:
    """Dataclass holding a value with optional units and description.

    Setters silently ignore values of the wrong type; comparisons and
    arithmetic convert operands to this parameter's units via pint.
    """

    value: object | None = None
    units: str | None = None
    description: str | None = None

    _value: object = field(init=False, default=None, repr=False)
    _units: str = field(init=False, default="", repr=False)
    _description: str = field(init=False, default="", repr=False)

    # def __init__(self, value=None, units=None):
    #     pass
    #
    # def __post_init__(self):
    #     if not self.units:
    #         self._units = ""

    @property
    def value(self) -> object:  # noqa: F811
        """Current value of the parameter."""
        return self._value

    @value.setter
    def value(self, value: object):
        if not isinstance(value, (int, float, str, tuple)):
            return

        if isinstance(value, tuple):
            self._value, self._units = value
            return

        self._value = value

    @property
    def units(self) -> str:  # noqa: F811
        """Units of the value as a string (empty string if unset)."""
        return self._units

    @units.setter
    def units(self, units: str):
        if not isinstance(units, str):
            return
        self._units = units

    @property
    def description(self) -> str:  # noqa: F811
        """Human-readable description (empty string if unset)."""
        return self._description

    @description.setter
    def description(self, description: str):
        if not isinstance(description, str):
            return
        self._description = description

    def to_dict(self):
        """Return the public fields as a dict.

        Private fields are skipped, and empty-string values (the
        defaults for ``units`` and ``description``) are omitted.

        Returns:
            dict: Mapping of field names to their current values.
        """
        data = {}
        for raw_field in fields(self):
            if raw_field.name.startswith("_"):
                continue
            attribute = getattr(self, raw_field.name)
            if attribute != "":  # guard against default empty values
                data[raw_field.name] = attribute
        return data

    def to_units_system(self, new_system):
        """
        Convert this quantity to a new unit system and return a new object.

        Args:
            new_system (str): Target unit system, e.g., 'SI', 'imperial'.

        Returns:
            New instance of the same class with converted value and units.
        """
        import pint
        quantity = UREG.Quantity(self.value, self.units)

        # Convert to base units first
        quantity_base = quantity.to_base_units()

        # Select units for the target system
        if new_system.lower() == 'si':
            # Keep base units (pint uses SI as default)
            target_units = quantity_base.units
        elif new_system.lower() == 'imperial':
            # Convert to imperial units
            # You may need to define a mapping from SI to imperial for your quantities
            # Example: meters -> feet, kilograms -> pounds
            try:
                target_units = (quantity_base.to('feet').units
                                if quantity_base.dimensionality == UREG.meter.dimensionality
                                else quantity_base.units)
            except pint.DimensionalityError:
                target_units = quantity_base.units  # fallback
        else:
            raise ValueError(f"Unknown unit system: {new_system}")

        # Convert quantity to target units
        converted = quantity_base.to(target_units)

        # Format units string if needed
        units = self._format_units_strict(converted.units)

        # Return a new object of the same class
        return self.__class__(converted.magnitude, units)

    def to_units(self, new_units):
        """returns new object"""
        quantity = UREG.Quantity(self.value, self.units)
        converted = quantity.to(new_units)
        units = self._format_units_strict(converted.units)
        return self.__class__(converted.magnitude, units)

    def ito_units(self, new_units):  # i = in-place
        """changes this object"""
        if self.units == new_units:
            return self

        quantity = UREG.Quantity(self.value, self.units)
        converted = quantity.to(new_units)

        self.value = converted.magnitude
        self.units = self._format_units_strict(converted.units)

        return self

    def _format_units_strict(self, units) -> str:
        parts = []

        # units._units is a dict like {'meter': 1, 'second': -2}
        for unit_name, power in units._units.items():
            symbol = UREG.get_symbol(unit_name)

            if power == 1:
                parts.append(symbol)
            else:
                parts.append(f"{symbol}^{int(power)}")

        return "*".join(parts)

    def __float__(self):
        # return float(self._quantity.magnitude)
        return float(self._value)

    def __int__(self):
        return int(self._value)
        # return int(self._quantity.magnitude)

    def __str__(self):
        # return f"{self._quantity:~P}"
        return f"{self._value}"

    def __abs__(self):
        return self.__class__(abs(self.value), f"{self.units}", self.description)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if UREG(self.units).is_compatible_with(UREG(other.units)):
                converted_other_value = other.ito_units(self.units).value
                return self.value == converted_other_value
            else:
                return False
        elif isinstance(other, (int, float)):
            return self.value == other
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if UREG(self.units).is_compatible_with(UREG(other.units)):
                converted_other_value = other.ito_units(self.units).value
                return self.value < converted_other_value
            else:
                raise TypeError(f"Units do not match: {self.units}, {other.units}")
        elif isinstance(other, (int, float)):
            return self.value < other
        else:
            return False

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__lt__(other) and not self.__eq__(other)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            if (UREG(self.units).is_compatible_with(UREG(other.units))
                    or (self.units == other.units == "")):
                converted_other_value = other.ito_units(self.units).value
                sum_value = self.value + converted_other_value
                return self.__class__(sum_value, f"{self.units}")
            else:
                raise TypeError(f"Units do not match: {self.units}, {other.units}")
        elif isinstance(other, (int, float)):
            return self.__class__(self.value + other, f"{self.units}")

    def __radd__(self, other):
        return self.__add__(other)

    def __neg__(self):
        return self.__class__(-self.value, f"{self.units}", self.description)

    def __sub__(self, other):
        return self.__add__(-other)

    def __rsub__(self, other):
        return self.__neg__().__add__(other)

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            if self.units and other.units:
                units = f"{self.units}*{other.units}"
            elif self.units and not other.units:
                units = f"{self.units}"
            elif not self.units and other.units:
                units = f"{other.units}"
            else:
                units = ""
            return self.__class__(self.value * other.value, units)
        elif isinstance(other, (int, float)):
            return self.__class__(self.value * other, f"{self.units}")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __pow__(self, power, modulo=None):
        return self.__class__(self.value**power,
                              f"({self.units})^{power}" if self.units else "")

    def __truediv__(self, other):
        return self * (other ** -1)
