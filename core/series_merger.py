import pandas as pd
import itertools


def series_merger(*series_list, reset_index=True, sort=False):
    """
    Выполняет cross merging (декартово произведение) нескольких Series в один DataFrame

    Parameters:
    *series_list: переменное количество Series
    reset_index: сбросить индекс или оставить MultiIndex
    sort: сортировать результат
    """
    if not series_list:
        return pd.DataFrame()

    names = [s.name for s in series_list]
    values = [s.values for s in series_list]

    # Проверяем, что все Series имеют имена
    if any(name is None for name in names):
        raise ValueError("All Series must have names for cross merge")

    # Создаем декартово произведение
    cartesian_product = list(itertools.product(*values))

    if sort:
        cartesian_product.sort()

    df = pd.DataFrame(cartesian_product, columns=names)

    # Приводим типы
    for series, col_name in zip(series_list, names):
        df[col_name] = df[col_name].astype(series.dtype)

    if not reset_index:
        df.set_index(names, inplace=True)

    return df
