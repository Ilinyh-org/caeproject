"""Tests for the ``core.series_merger.series_merger`` cross-merge utility.

Covers cartesian-product merging of named pandas Series, sorting,
reset_index behaviour, dtype preservation, edge cases (empty, single,
NaN, duplicate values) and error handling for unnamed series.
"""
import math

import numpy as np
import pandas as pd
import pytest

from core.series_merger import series_merger


# ============ Fixtures ============

@pytest.fixture
def basic_series():
    """Basic series for testing"""
    return {
        'H1': pd.Series([1, 2], dtype='float64', name="H1"),
        'B1': pd.Series([1], dtype='float64', name="B1"),
        'L1': pd.Series([10], dtype='float64', name="L1"),
        'NES_H1': pd.Series([2], dtype='int64', name="NES_H1"),
        'NES_B1': pd.Series([2], dtype='int64', name="NES_B1"),
        'NES_L1': pd.Series([20], dtype='int64', name="NES_L1")
    }


@pytest.fixture
def string_series():
    """Series with string values"""
    return {
        'letters1': pd.Series(['A', 'B', 'C'], name='letters'),
        'letters2': pd.Series(['X', 'Y'], name='letters2')
    }


@pytest.fixture
def mixed_type_series():
    """Series with mixed data types"""
    return {
        'ints': pd.Series([1, 2, 3], name='ints'),
        'strings': pd.Series(['a', 'b'], name='strings'),
        'floats': pd.Series([1.5, 2.5], name='floats'),
        'bools': pd.Series([True, False], name='bools')
    }


# ============ Basic Functionality Tests ============

def test_basic_cross_merge_two_series(basic_series):
    """Test basic cross merge with two series"""
    expected_rows = len(basic_series['H1']) * len(basic_series['B1'])
    expected_columns_names = ['H1', 'B1']
    expected_types = ['float64', 'float64']

    actual_result = series_merger(basic_series['H1'], basic_series['B1'])

    assert len(actual_result) == expected_rows
    assert list(actual_result.columns) == expected_columns_names
    assert [actual_result[column].dtype for column in expected_columns_names] == expected_types


def test_cross_merge_multiple_series(basic_series):
    """Test cross merge with three series"""
    eps = 1E-4
    expected_rows = len(basic_series['H1']) * len(basic_series['B1']) * len(basic_series['L1'])
    expected_combinations = [(1, 1, 10), (2, 1, 10)]
    expected_columns_names = ['H1', 'B1', 'L1']

    actual_result = series_merger(basic_series['H1'], basic_series['B1'], basic_series['L1'])

    assert len(actual_result) == expected_rows
    assert list(actual_result.columns) == expected_columns_names
    for i in range(len(expected_combinations)):
        assert tuple(actual_result.iloc[i]) == pytest.approx(expected_combinations[i], abs=eps)


def test_cross_merge_all_six_series(basic_series):
    """Test cross merge with all six series"""
    expected_columns = ['H1', 'B1', 'L1', 'NES_H1', 'NES_B1', 'NES_L1']
    # multiplication of series lens
    expected_rows = math.prod([len(basic_series[column]) for column in expected_columns])

    actual_result = series_merger(*list(basic_series[column] for column in expected_columns))

    assert len(actual_result) == expected_rows
    assert len(actual_result.columns) == len(expected_columns)
    assert list(actual_result.columns) == expected_columns

# ============ Sort Parameter Tests ============

def test_cross_merge_with_sort():
    """Test cross merge with sorting enabled"""
    unsorted_series1 = pd.Series([3, 1, 2], name='numbers')
    unsorted_series2 = pd.Series(['c', 'a', 'b'], name='letters')

    result_sorted = series_merger(unsorted_series1, unsorted_series2, sort=True)

    # Check if sorted by first column then second
    first_col_values = result_sorted['numbers'].tolist()
    assert first_col_values == sorted(first_col_values)


def test_cross_merge_without_sort():
    """Test cross merge without sorting (order preservation)"""
    series1 = pd.Series([3, 1, 2], name='numbers')
    series2 = pd.Series(['c', 'a', 'b'], name='letters')

    result_unsorted = series_merger(series1, series2, sort=False)

    # Cartesian product in original order: (3,c), (3,a), (3,b),
    # (1,c), (1,a), (1,b), (2,c), (2,a), (2,b)
    assert result_unsorted.iloc[0]['numbers'] == 3
    assert result_unsorted.iloc[0]['letters'] == 'c'


def test_sort_with_different_types():
    """Test sorting with different data types"""
    num_series = pd.Series([3, 1, 2], name='numbers')
    str_series = pd.Series(['c', 'a', 'b'], name='strings')

    result = series_merger(num_series, str_series, sort=True)

    # Check first column is sorted
    first_col = result['numbers'].tolist()
    assert first_col == sorted(first_col)

    # Within same first column, second column should be sorted
    first_unique = result['numbers'].unique()
    for val in first_unique:
        subset = result[result['numbers'] == val]['strings'].tolist()
        assert subset == sorted(subset)


# ============ Reset Index Parameter Tests ============

def test_reset_index_true(basic_series):
    """Test reset_index=True (default behavior)"""
    result = series_merger(basic_series['H1'], basic_series['B1'], reset_index=True)

    assert isinstance(result.index, pd.RangeIndex)
    assert result.index.name is None
    assert len(result) == 2


def test_reset_index_false(basic_series):
    """Test reset_index=False (MultiIndex)"""
    result = series_merger(basic_series['H1'], basic_series['B1'], reset_index=False)

    assert isinstance(result.index, pd.MultiIndex)
    assert result.index.names == ['H1', 'B1']
    assert len(result) == 2


def test_reset_index_false_multiple_series(basic_series):
    """Test reset_index=False with multiple series"""
    result = series_merger(basic_series['H1'], basic_series['B1'], basic_series['L1'],
                          reset_index=False)

    assert isinstance(result.index, pd.MultiIndex)
    assert result.index.names == ['H1', 'B1', 'L1']
    assert len(result) == 2


# ============ Data Type Tests ============

def test_preserve_float_dtype(basic_series):
    """Test that float data types are preserved"""
    result = series_merger(basic_series['H1'], basic_series['B1'])

    assert result['H1'].dtype == 'float64'
    assert result['B1'].dtype == 'float64'


def test_preserve_int_dtype(basic_series):
    """Test that integer data types are preserved"""
    result = series_merger(basic_series['NES_H1'], basic_series['NES_B1'])

    assert result['NES_H1'].dtype == 'int64'
    assert result['NES_B1'].dtype == 'int64'


def test_preserve_mixed_types(mixed_type_series):
    """Test that mixed data types are preserved"""
    result = series_merger(
        mixed_type_series['ints'],
        mixed_type_series['strings'],
        mixed_type_series['floats'],
        mixed_type_series['bools']
    )

    assert result['ints'].dtype == 'int64'
    assert result['strings'].dtype == "string"
    assert result['floats'].dtype == 'float64'
    assert result['bools'].dtype == 'bool'


def test_string_series(string_series):
    """Test cross merge with string series"""
    result = series_merger(string_series['letters1'], string_series['letters2'])

    expected_rows = len(string_series['letters1']) * len(string_series['letters2'])
    assert len(result) == expected_rows
    assert all(isinstance(val, str) for val in result['letters'])
    assert all(isinstance(val, str) for val in result['letters2'])


# ============ Edge Cases Tests ============

def test_empty_input():
    """Test with empty input"""
    result = series_merger()
    assert result.empty
    assert len(result) == 0


def test_single_series(basic_series):
    """Test with single series"""
    result = series_merger(basic_series['H1'])

    assert len(result) == len(basic_series['H1'])
    assert list(result.columns) == ['H1']
    assert (result['H1'] == basic_series['H1'].values).all()


def test_single_element_series():
    """Test with single element series"""
    s1 = pd.Series([1], name='a')
    s2 = pd.Series([2], name='b')
    s3 = pd.Series([3], name='c')

    result = series_merger(s1, s2, s3)

    assert len(result) == 1
    assert result.iloc[0].tolist() == [1, 2, 3]


def test_zero_length_series(basic_series):
    """Test with empty series (but with name)"""
    empty_series = pd.Series([], dtype='float64', name='empty')

    result = series_merger(basic_series['H1'], empty_series)

    assert len(result) == 0
    assert list(result.columns) == ['H1', 'empty']


def test_nan_values_in_series():
    """Test with NaN values"""
    nan_series = pd.Series([1, np.nan, 3], name='with_nan')
    other_series = pd.Series(['a', 'b'], name='letters')

    result = series_merger(nan_series, other_series)

    expected_rows = 3 * 2
    assert len(result) == expected_rows
    assert pd.isna(result['with_nan']).any()


def test_duplicate_values_in_series():
    """Test cross merge with duplicate values in series"""
    dup_series1 = pd.Series([1, 1, 2], name='dups1')
    dup_series2 = pd.Series(['a', 'a'], name='dups2')

    result = series_merger(dup_series1, dup_series2)

    expected_rows = len(dup_series1) * len(dup_series2)
    assert len(result) == expected_rows

    # Check that duplicates are preserved
    assert result['dups1'].tolist() == [1, 1, 1, 1, 2, 2]
    assert result['dups2'].tolist() == ['a', 'a', 'a', 'a', 'a', 'a']


# ============ Error Handling Tests ============

def test_series_without_names_raises_error():
    """Test that series without names raise ValueError"""
    named_series = pd.Series([1, 2], name='named')
    unnamed_series = pd.Series([1, 2, 3])

    with pytest.raises(ValueError, match="All Series must have names for cross merge"):
        series_merger(named_series, unnamed_series)


def test_all_series_without_names_raises_error():
    """Test that all series without names raise ValueError"""
    unnamed_series1 = pd.Series([1, 2])
    unnamed_series2 = pd.Series([3, 4])

    with pytest.raises(ValueError, match="All Series must have names for cross merge"):
        series_merger(unnamed_series1, unnamed_series2)


def test_mixed_named_and_unnamed_raises_error(basic_series):
    """Test that mixing named and unnamed series raises ValueError"""
    unnamed_series = pd.Series([1, 2, 3])

    with pytest.raises(ValueError, match="All Series must have names for cross merge"):
        series_merger(basic_series['H1'], unnamed_series)


# ============ Correctness Tests ============

def test_cartesian_product_correctness():
    """Test that all combinations are exactly the cartesian product"""
    series_a = pd.Series([1, 2], name='A')
    series_b = pd.Series(['x', 'y', 'z'], name='B')

    result = series_merger(series_a, series_b, sort=True)

    # Generate expected cartesian product
    expected = pd.DataFrame(
        [(a, b) for a in [1, 2] for b in ['x', 'y', 'z']],
        columns=['A', 'B']
    )

    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected)


def test_cartesian_product_order_without_sort():
    """Test cartesian product order when sort=False"""
    series_a = pd.Series([1, 2], name='A')
    series_b = pd.Series(['x', 'y'], name='B')

    result = series_merger(series_a, series_b, sort=False)

    # Order should be: (1,x), (1,y), (2,x), (2,y)
    assert result.iloc[0]['A'] == 1
    assert result.iloc[0]['B'] == 'x'
    assert result.iloc[1]['A'] == 1
    assert result.iloc[1]['B'] == 'y'
    assert result.iloc[2]['A'] == 2
    assert result.iloc[2]['B'] == 'x'
    assert result.iloc[3]['A'] == 2
    assert result.iloc[3]['B'] == 'y'


# ============ Parameter Combination Tests ============

@pytest.mark.parametrize("reset_index, sort", [
    (True, True),
    (True, False),
    (False, True),
    (False, False)
])
def test_parameter_combinations(reset_index, sort, basic_series):
    """Test all combinations of reset_index and sort parameters"""
    result = series_merger(basic_series['H1'], basic_series['B1'],
                          reset_index=reset_index, sort=sort)

    expected_rows = len(basic_series['H1']) * len(basic_series['B1'])
    assert len(result) == expected_rows

    if reset_index:
        assert isinstance(result.index, pd.RangeIndex)
    else:
        assert isinstance(result.index, pd.MultiIndex)
        assert result.index.names == ['H1', 'B1']


# ============ Helper function to run tests ============

if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
