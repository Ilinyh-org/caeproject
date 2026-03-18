
from caecase import Parameter, Node


def test_parameter_creation_via_structure_attribute():
    input_value = 10
    expected_repr = "Parameter(value=10, units='', description='')"
    node = Node()

    node.x = input_value

    actual_repr = repr(node.x)
    assert actual_repr == expected_repr


def test_parameter_creation_via_structure_attribute2():
    input_value = 10
    expected_repr = "Parameter(value=10, units='', description='')"
    node = Node()

    node.x.value = input_value

    actual_repr = repr(node.x)
    assert actual_repr == expected_repr


def test_node_to_dict_with_metadata():
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