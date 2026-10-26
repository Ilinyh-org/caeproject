"""Tests for the APDLConverter data converter."""
import pytest

from data_converter import APDLConverter


@pytest.mark.parametrize("input_data, expected_result",
                         [({'A':5,'B':7},'A=5\nB=7\n'),
                          ({'category 1':{'A': 5, 'B':6}, 'C': 7}, '!category 1\nA=5\nB=6\nC=7\n'),
                          ({'category 1':{'subcategory 1':{'A': 5}, 'subcategory 2':{'B': 7}},'category 2':{'C':8}},
                           '!category 1\n!!subcategory 1\nA=5\n!!subcategory 2\nB=7\n!category 2\nC=8\n'),
                          ({'A':{"value": 5,"units": "cm",},'B':7},'A=5 ![cm]\nB=7\n'),
                          ])
def test_convert(input_data, expected_result):
    """Verify flat, nested and unit-annotated dicts render as APDL parameter text."""
    data_converter = APDLConverter()

    actual_result = data_converter.convert(input_data)

    assert actual_result == expected_result

