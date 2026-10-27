
"""Unit tests for core.parameter.Parameter: initialization, unit conversion, metadata, serialization, arithmetic and comparisons."""
from pint import UnitRegistry
import pytest

from core.parameter import Parameter

EPS = 1e-3

@pytest.mark.parametrize("input_value, expected_value", [
    (10, 10),
    (5.5, 5.5),
    ((20, "m"), 20),
])
def test_parameter_initialization_value(input_value, expected_value):
    """Verify Parameter accepts scalars and (value, unit) tuples keeping the numeric value."""
    p = Parameter(value=input_value)

    actual_value = p.value
    assert actual_value == expected_value


@pytest.mark.parametrize("input_value, input_units, expected_units", [
    (23, "m", "m"),
    (1e5, "Pa", "Pa"),
    (2, "atm", "atm"),
    (1500, "s^-1", "s^-1"),
])
def test_parameter_initialization_units(input_value, input_units, expected_units):
    """Verify the units attribute stores the given units string."""
    p = Parameter(value=input_value, units=input_units)

    actual_units = p.units
    assert actual_units == expected_units


@pytest.mark.parametrize("input_value, expected_value, expected_units", [
    ((2, "s"), 2, "s"),
    ((2, "km"), 2000, "m"),
    ((1.8, "km"), 1800, "m"),
    ((3600, "h^-1"), 1, "s^-1"),
    ((3600*3600, "m * h^-2"), 1, "m*s^-2"),
])
def test_parameter_get_value_with_iconversion(input_value, expected_value, expected_units):
    """Verify ito_units converts value and units in place."""
    p = Parameter(value=input_value)

    p.ito_units(expected_units)

    actual_value = p.value
    actual_units = p.units
    assert actual_value == pytest.approx(expected_value, abs=EPS)
    assert actual_units == expected_units


@pytest.mark.parametrize("input_value, expected_value, expected_units", [
    ((2, "s"), 2, "s"),
    ((2, "km"), 2000, "m"),
    ((1.8, "km"), 1800, "m"),
    ((3600, "h^-1"), 1, "s^-1"),
    ((3600*3600, "m * h^-2"), 1, "m*s^-2"),
])
def test_parameter_get_value_with_conversion(input_value, expected_value, expected_units):
    """Verify to_units returns a converted Parameter."""
    p = Parameter(value=input_value)

    p = p.to_units(expected_units)

    actual_value = p.value
    actual_units = p.units
    assert actual_value == pytest.approx(expected_value, abs=EPS)
    assert actual_units == expected_units


@pytest.mark.parametrize("input_value, input_system, expected_value, expected_units", [
    ((3, "min"), "SI", 180, "s"),
    ((2, "km"), "SI", 2000, "m"),
    ((20, "m"), "SI", 20, "m"),
    ((1, "m"), "imperial", 3.280, "ft"),
    ((3600, "h^-1"), 'si', 1, "s^-1"),
    ((3600*3600, "m * h^-2"), 'si', 1, "m*s^-2"),
])
def test_parameter_get_value_with_system_conversion(input_value, input_system, expected_value, expected_units):
    """Verify to_units_system converts to the target unit system (SI/imperial)."""
    p = Parameter(value=input_value)

    p = p.to_units_system(input_system)

    actual_value = p.value
    actual_units = p.units
    assert actual_value == pytest.approx(expected_value, abs=EPS)
    assert actual_units == expected_units


def test_parameter_initialization_default_units():
    """Verify units default to an empty string."""
    input_value = 10
    expected_units = ""

    p = Parameter(value=input_value)

    actual_units = p.units
    assert actual_units == expected_units


@pytest.mark.parametrize("input_value, expected_repr", [
    (5.5, "Parameter(value=5.5, units='', description='')"),
    ((20, "m"), "Parameter(value=20, units='m', description='')"),
    # (ureg.Quantity(300, "kg"), "Parameter(value=300, units='kg', description='')"),
])
def test_parameter_initialization_repr(input_value, expected_repr):
    """Verify repr shows value, units and empty description."""
    p = Parameter(value=input_value)

    actual_repr = repr(p)

    assert actual_repr == expected_repr


@pytest.mark.parametrize("input_value, expected_repr", [
    (70, "Parameter(value=70, units='', description='')"),
    ((20, "m"), "Parameter(value=20, units='m', description='')"),
])
def test_parameter_initialization(input_value, expected_repr):
    """Verify positional initialization produces the expected repr."""
    p = Parameter(input_value)

    actual_repr = repr(p)

    assert actual_repr == expected_repr


def test_parameter_initialization_empty():
    """Verify a Parameter without arguments has value None."""
    expected_repr = "Parameter(value=None, units='', description='')"

    p = Parameter()

    actual_repr = repr(p)
    assert actual_repr == expected_repr


@pytest.mark.parametrize("input_value, expected_repr", [
    (10, "Parameter(value=10, units='', description='')"),
    ((20, "m"), "Parameter(value=20, units='m', description='')"),
])
def test_parameter_set_value_attribute(input_value, expected_repr):
    """Verify assigning the value attribute updates the repr."""
    p = Parameter()

    p.value = input_value

    actual_repr = repr(p)
    assert actual_repr == expected_repr


def test_parameter_creation_via_structure():
    """Verify Parameter can be stored inside a simple structure attribute."""
    class Node:
        """Minimal holder struct storing a Parameter."""

        def __init__(self, value):
            self.parameter = Parameter(value)
    input_value = 10
    expected_repr = "Parameter(value=10, units='', description='')"

    node = Node(input_value)

    actual_repr = repr(node.parameter)
    assert actual_repr == expected_repr


def test_parameter_with_metadata():
    """Verify metadata kwargs (units, description) appear in the repr."""
    input_value = 5.5
    input_metadata = {"units": "mm", "description": "Толщина"}
    expected_repr = "Parameter(value=5.5, units='mm', description='Толщина')"

    p = Parameter(input_value, **input_metadata)

    actual_repr = repr(p)
    assert actual_repr == expected_repr


@pytest.mark.parametrize("input_value, conversion_function, expected_value", [
    (10.1, int, 10),
    ("10.1", float, 10.1),
    (-55.5, str, "-55.5"),
])
def test_parameter_type_conversion(input_value, conversion_function, expected_value):
    """Verify int/float/str conversions return the underlying value converted."""
    p = Parameter(input_value)

    actual_value = conversion_function(p)

    assert actual_value == expected_value


@pytest.mark.parametrize("input_value, expected_value", [
    (10.1, {'value': 10.1}),
    (0, {'value': 0}),
    ("a", {'value': "a"}),
    ("", {}),
])
def test_parameter_to_dict(input_value, expected_value):
    """Verify to_dict returns {'value': ...} and {} for an empty value."""
    p = Parameter(input_value)

    actual_value = p.to_dict()

    assert actual_value == expected_value


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((20, "m"), (3, "m"), Parameter(value=23, units='m', description='')),
    ((-1, "s"), (3, "s"), Parameter(value=2, units='s', description='')),
    ((1, "h"), (30, "min"), Parameter(value=1.5, units='h', description='')),
    ((30, "min"), (2, "h"), Parameter(value=150, units='min', description='')),
])
def test_parameters_arithmetic_sum(input_value1, input_value2, expected_result):
    """Verify Parameter + Parameter sums values with unit conversion."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_sum = p1 + p2

    assert abs(actual_sum - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2", [
    ((20, ""), (3, "m")),
    ((-1, "kg"), (3, "s")),
])
def test_parameters_arithmetic_sum_wrong_types(input_value1, input_value2):
    """Verify adding parameters with incompatible units raises TypeError."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    with pytest.raises(TypeError):
        p1 + p2


def test_parameter_arithmetic_unary_minus():
    """Verify unary minus negates the value keeping units."""
    input_value = (20, "m")
    p = Parameter(input_value)
    expected_result = Parameter(value=-20, units='m', description='')

    actual_result = -p

    assert actual_result == expected_result


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((20, "m"), 3, Parameter(value=23, units='m', description='')),
    ((3, "s"), 3.2, Parameter(value=6.2, units='s', description='')),
])
def test_parameter_number_arithmetic_sum(input_value1, input_value2, expected_result):
    """Verify Parameter + number adds to the parameter's value."""
    p1 = Parameter(input_value1)

    actual_result = p1 + input_value2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((20, "m"), 3, Parameter(value=17, units='m', description='')),
    ((3, "s"), 3.2, Parameter(value=-0.2, units='s', description='')),
])
def test_parameter_number_arithmetic_sub(input_value1, input_value2, expected_result):
    """Verify Parameter - number subtracts from the parameter's value."""
    p1 = Parameter(input_value1)

    actual_result = p1 - input_value2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    (21, (19, "m"), Parameter(value=2, units='m', description='')),
    (4.2, (3, "s"), Parameter(value=1.2, units='s', description='')),
])
def test_number_parameter_arithmetic_sub(input_value1, input_value2, expected_result):
    """Verify number - Parameter subtracts the parameter's value."""
    p2 = Parameter(input_value2)

    actual_result = input_value1 - p2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    (4 , (21, "m"), Parameter(value=25, units='m', description='')),
    (-2.2, (3, "s"), Parameter(value=0.8, units='s', description='')),
])
def test_number_parameter_arithmetic_sum(input_value1, input_value2, expected_result):
    """Verify number + Parameter adds the parameter's value."""
    p2 = Parameter(input_value2)

    actual_result = input_value1 + p2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    (4 , (21, "Pa"), Parameter(value=84, units='Pa', description='')),
    (-2.2, (3, "Pa s"), Parameter(value=-6.6, units='Pa s', description='')),
])
def test_number_parameter_arithmetic_multiplication(input_value1, input_value2, expected_result):
    """Verify number * Parameter scales the value keeping units."""
    p2 = Parameter(input_value2)

    actual_result = input_value1 * p2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((4.2, "V"), 4, Parameter(value=16.8, units='V', description='')),
    ((3, "N"), 5.1, Parameter(value=15.3, units='N', description='')),
])
def test_parameter_number_arithmetic_multiplication(input_value1, input_value2, expected_result):
    """Verify Parameter * number scales the value keeping units."""
    p1 = Parameter(input_value1)

    actual_result = p1 * input_value2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (2, "s"), Parameter(value=2.4, units='Pa s', description='')),
    ((3, "kg"), (-2, "m s^-1"), Parameter(value=-6, units='kg*m*s^-1', description='')),
    ((2, ""), (2, "A"), Parameter(value=4, units='A', description='')),
    ((4, "W"), (1.5, ""), Parameter(value=6, units='W', description='')),
    ((16, ""), (0.5, ""), Parameter(value=8, units='', description='')),
])
def test_parameters_arithmetic_multiplication(input_value1, input_value2, expected_result):
    """Verify Parameter * Parameter multiplies values and combines units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 * p2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((4, "s"), 2, Parameter(value=16, units='s^2', description='')),
    ((2, ""), 3, Parameter(value=8, units='', description='')),
])
def test_parameter_number_arithmetic_power(input_value1, input_value2, expected_result):
    """Verify Parameter ** number raises the value and units to the power."""
    p1 = Parameter(input_value1)

    actual_result = p1 ** input_value2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((5, "s"), 2, Parameter(value=2.5, units='s', description='')),
    ((2.2, ""), 2, Parameter(value=1.1, units='', description='')),
])
def test_parameter_number_arithmetic_division(input_value1, input_value2, expected_result):
    """Verify Parameter / number divides the value keeping units."""
    p1 = Parameter(input_value1)

    actual_result = p1 / input_value2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (2, "s"), Parameter(value=0.6, units='Pa s^-1', description='')),
    ((5, "kg"), (-2, ""), Parameter(value=-2.5, units='kg', description='')),
])
def test_parameters_arithmetic_division(input_value1, input_value2, expected_result):
    """Verify Parameter / Parameter divides values and combines units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 / p2

    assert abs(actual_result - expected_result) <= EPS


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (1.2, "Pa"), True),
    ((5, "kg"), (5, ""), False),
    ((5, "kg"), (5.01, "kg"), False),
])
def test_parameters_comparison_eq(input_value1, input_value2, expected_result):
    """Verify == compares value and units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 == p2

    assert actual_result == expected_result


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), 1.2 , True),
    ((5, "kg"), 5, True),
    ((5, "kg"), 5.01, False),
])
def test_parameter_number_comparison_eq(input_value1, input_value2, expected_result):
    """Verify Parameter == number compares the bare value."""
    p1 = Parameter(input_value1)

    actual_result = p1 == input_value2

    assert actual_result == expected_result


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (1.2, "Pa"), False),
    ((5, "kg"), (5, ""), True),
    ((5, "kg"), (5.01, "kg"), True),
])
def test_parameters_comparison_ne(input_value1, input_value2, expected_result):
    """Verify != negates equality including unit mismatches."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 != p2

    assert actual_result == expected_result


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (2.2, "Pa"), True),
    ((1.2, "Pa s"), (1.2, "Pa s"), True),
    ((5, "V"), (2, "V"), False),
    ((5.02, "kg"), (5.01, "kg"), False),
])
def test_parameters_comparison_le(input_value1, input_value2, expected_result):
    """Verify <= compares parameters of compatible units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 <= p2

    assert actual_result == expected_result


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (2.2, "Pa"), False),
    ((1.2, "Pa s"), (1.2, "Pa s"), True),
    ((5, "V"), (2, "V"), True),
    ((5.02, "kg"), (5.01, "kg"), True),
])
def test_parameters_comparison_ge(input_value1, input_value2, expected_result):
    """Verify >= compares parameters of compatible units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 >= p2

    assert actual_result == expected_result

@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (2.2, "Pa"), True),
    ((1.2, "Pa s"), (1.2, "Pa s"), False),
    ((5, "V"), (2, "V"), False),
    ((5.02, "kg"), (5.01, "kg"), False),
])
def test_parameters_comparison_lt(input_value1, input_value2, expected_result):
    """Verify < compares parameters of compatible units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 < p2

    assert actual_result == expected_result


@pytest.mark.parametrize("input_value1, input_value2", [
    ((20, ""), (3, "m")),
    ((-1, "kg"), (3, "s")),
])
def test_parameters_arithmetic_lt_wrong_types(input_value1, input_value2):
    """Verify comparing incompatible units with < raises TypeError."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    with pytest.raises(TypeError):
        p1 < p2


@pytest.mark.parametrize("input_value1, input_value2, expected_result", [
    ((1.2, "Pa"), (2.2, "Pa"), False),
    ((1.2, "Pa s"), (1.2, "Pa s"), False),
    ((5, "V"), (2, "V"), True),
    ((5.02, ""), (5.01, ""), True),
])
def test_parameters_comparison_gt(input_value1, input_value2, expected_result):
    """Verify > compares parameters of compatible units."""
    p1 = Parameter(input_value1)
    p2 = Parameter(input_value2)

    actual_result = p1 > p2

    assert actual_result == expected_result
