
"""Integration tests for Parameter creation via Node attributes and Node serialization with metadata."""
from core.parameter import Parameter
from core.node import Node


def test_parameter_creation_via_structure_attribute():
    """Verify assigning a plain value to a Node attribute produces a Parameter with that value."""
    input_value = 10
    expected_repr = "Parameter(value=10, units='', description='')"
    node = Node()

    node.x = input_value

    actual_repr = repr(node.x)
    assert actual_repr == expected_repr


def test_parameter_creation_via_structure_attribute2():
    """Verify setting value on a Node attribute Parameter keeps the default units/description repr."""
    input_value = 10
    expected_repr = "Parameter(value=10, units='', description='')"
    node = Node()

    node.x.value = input_value

    actual_repr = repr(node.x)
    assert actual_repr == expected_repr


def test_node_to_dict_with_metadata():
    """Verify Node.to_dict serializes a Parameter with its value, units and description."""
    input_value = 0.1
    input_metadata = {'description': 'some text', 'units': 'm'}
    expected_dict = {
        "param": {
            "value": 0.1,
            "units": "m",
            "description": "some text"
        }
    }
    node = Node()
    p = Parameter(input_value, **input_metadata)
    node.param = p
    print(type(node.param))
    actual_dict = node.to_dict()

    assert actual_dict == expected_dict