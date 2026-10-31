"""Helper for cross-merging named pandas Series into a DataFrame."""
import itertools

import pandas as pd


def series_merger(*series_list, reset_index=True, sort=False):
    """
    Performs cross merging (Cartesian product) of several Series into one DataFrame

    Parameters:
    *series_list: variable number of Series
    reset_index: reset the index or keep the MultiIndex
    sort: sort the result
    """
    if not series_list:
        return pd.DataFrame()

    names = [s.name for s in series_list]
    values = [s.values for s in series_list]

    # Check that all Series have names
    if any(name is None for name in names):
        raise ValueError("All Series must have names for cross merge")

    # Create the Cartesian product
    cartesian_product = list(itertools.product(*values))

    if sort:
        cartesian_product.sort()

    df = pd.DataFrame(cartesian_product, columns=names)

    # Cast types
    for series, col_name in zip(series_list, names):
        df[col_name] = df[col_name].astype(series.dtype)

    if not reset_index:
        df.set_index(names, inplace=True)

    return df
