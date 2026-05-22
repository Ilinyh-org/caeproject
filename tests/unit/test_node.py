
# from core import Node, Parameter
from core.parameter import Parameter
from core.node import Node
import pytest

def test_node_initialization_by_attributes():
    input_value = 100
    expected_value = input_value
    node = Node()

    node.a.b.c = input_value

    actual_value = node.a.b.c.value
    assert actual_value == expected_value


def test_node_get_value_by_name():
    input_value = 8
    expected_value = input_value
    expected_type = Parameter
    node = Node()
    node.a.b.c = input_value

    actual_value = node.a.b.c
    actual_type = type(actual_value)

    assert actual_type == expected_type
    assert actual_value == expected_value

@pytest.mark.parametrize("input_value, expected_type", [
    (8, int),
    (3.5, float),
])
def test_node_get_value_by_value_attribute(input_value, expected_type):
    expected_value = input_value
    node = Node()
    node.a.b.c = input_value

    actual_value = node.a.b.c.value
    actual_type = type(actual_value)

    assert actual_type == expected_type
    assert actual_value == expected_value


def test_node_get_value_in_loop_list():
    expected_result = [0, 1, 2]
    nodes = []
    for i in range(3):
        nodes.append(Node())
        nodes[len(nodes) - 1].a = i

    actual_result = [node.a for node in nodes]

    assert actual_result == expected_result


def test_node_get_value_in_loop_set():
    expected_result = {0, 1, 2}
    nodes = []
    for i in range(3):
        nodes.append(Node())
        nodes[len(nodes) - 1].a = i

    actual_result = {node.a.value for node in nodes}

    assert actual_result == expected_result


def test_node_initialization_by_keys():
    input_value = 42
    expected_value = input_value
    node = Node()

    node["x"]["y"]["z"] = input_value

    actual_value = node["x"]["y"]["z"].value
    assert actual_value == expected_value


def test_node_initialization_two_branches():
    input_value_a = 1.5
    input_value_b = "test"
    expected_value_a = input_value_a
    expected_value_b = input_value_b
    node = Node()

    node.foo.a = input_value_a
    node["foo"]["b"] = input_value_b

    actual_value_a = node.foo.a.value
    actual_value_b = node.foo.b.value

    assert actual_value_a == expected_value_a
    assert actual_value_b == expected_value_b


def test_node_autocreate_nested():
    node = Node()
    KEY = "unknown"

    has_attr = hasattr(node, KEY)

    assert has_attr
    assert isinstance(node.unknown, Node)


def test_node_to_dict_simple():
    node = Node()
    node.x = 10
    node.y.z = "hello"
    expected_dict = {
        "x": {"value": 10},
        "y": {"z": {"value": "hello"}}
    }

    actual_dict = node.to_dict()

    assert actual_dict == expected_dict


def test_node_from_dict():
    node = Node()
    input_dict = {"a": {"b": {"value": 5, "units": "kg"}}}
    expected_value = 5
    expected_units = "kg"

    node.from_dict(input_dict)
    actual_value = node.a.b.value
    actual_units = node.a.b.units

    assert actual_value == expected_value
    assert actual_units == expected_units


@pytest.mark.parametrize("input_attr", [
    "shape",
    "dtype",
])
def test_node_no_recursion(input_attr):
    node = Node()

    node.a = 123

    with pytest.raises(AttributeError):
        getattr(node, input_attr)


