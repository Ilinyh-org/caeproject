#core/node.py
"""Hierarchical parameter tree node.

Provides :class:`Node`, a tree of named children holding
:class:`~core.parameter.Parameter` values, supporting attribute and
item access with auto-creation of nested nodes, and conversion to
dicts, DataFrames, or converted unit systems.
"""
from core.parameter import Parameter
import weakref
import pandas as pd


class Node:
    """
    Узел параметров.
    Поддерживает:
    - доступ через точку: node.a.b = 10
    - доступ через ключ: node["a"]["b"] = 10
    - автосоздание вложенных узлов
    """

    def __init__(self, name='', parent=None):
        self._name = name
        self._parent = weakref.ref(parent) if parent else None
        self._children = {}

    def __repr__(self):
        return f"Node({self._name}, {len(self._children)} children)"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._children == other._children

    def __getattr__(self, attr: str):
        # Block internal or forbidden attributes
        forbidden = ('shape', 'dtype', 'imag', 'real', 'conjugate', 'value')
        if attr.startswith('_') or attr in forbidden:
            raise AttributeError(attr)

        children = object.__getattribute__(self, '_children')

        # Return existing child if present
        if attr in children:
            return children[attr]

        # Auto-create valid identifier nodes
        if attr.isidentifier():
            new_node = Node(name=attr, parent=self)
            children[attr] = new_node
            return new_node

        raise AttributeError(attr)


    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        if name == 'value':
            self.parent[self._name] = Parameter(value)
            return

        # Если значение не Parameter — оборачиваем
        if isinstance(value, Parameter):
            self._children[name] = value
        else:
            self._children[name] = Parameter(value)

    def __getitem__(self, key):
        if key not in self._children:
            # Автосоздание узла, если ключа нет
            self._children[key] = Node()
        return self._packed(self._children[key])

    def __setitem__(self, key, value):
        if not isinstance(value, Parameter):
            value = Parameter(value)
        self._children[key] = value

    def _packed(self, obj):
        """Обертывает dict в ConfigNode, остальное оставляет как есть."""
        if isinstance(obj, dict):
            return Node().from_dict(obj)
        return obj

    def from_dict(self, d):
        """Заполняет узел из словаря."""
        for key, value in d.items():
            if isinstance(value, dict):
                if "value" in value:
                    # Это Parameter: есть "value" + возможно метаданные
                    params = {k: v for k, v in value.items() if k != "value"}
                    self._children[key] = Parameter(value["value"], **params)
                else:
                    # Это вложенный ConfigNode
                    if key not in self._children:
                        self._children[key] = Node()
                    self._children[key].from_dict(value)
            else:
                # Просто значение → оборачиваем в Parameter
                self._children[key] = Parameter(value)
        return self

    def to_dataframe(self, **filters) -> pd.DataFrame:
        """Convert the node tree to a single-row DataFrame.

        Column names are the leaf keys (e.g. 'A1', 'NES_A1'),
        values are the leaf values (Parameter.value or raw value).

        Accepts the same **filters as to_dict: 'include' and/or 'exclude'.
        """
        include = filters.get('include')
        exclude = filters.get('exclude')
        include_set = set(include) if include else None
        exclude_set = set(exclude) if exclude else None

        row = {}

        def walk(node):
            for key, value in node._children.items():
                if include_set is not None and key not in include_set:
                    continue
                if exclude_set is not None and key in exclude_set:
                    continue

                if isinstance(value, Node):
                    walk(value)
                elif isinstance(value, Parameter):
                    row[key] = value.value
                else:
                    row[key] = value

        walk(self)
        return pd.DataFrame([row])

    def to_dict(self, **filters):
        """Преобразует узел в обычный словарь.

        Args:
            **filters: Can include 'include' and/or 'exclude' keys
        """
        include = filters.get('include')
        exclude = filters.get('exclude')

        result = {}

        include_set = set(include) if include else None
        exclude_set = set(exclude) if exclude else None

        for key, value in self._children.items():
            if include_set is not None and key not in include_set:
                continue
            if exclude_set is not None and key in exclude_set:
                continue

            if isinstance(value, Node):
                result[key] = value.to_dict()
            elif isinstance(value, Parameter):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def to_units_system(self, **filters):
        """Recursively convert parameter units to a new unit system.

        Keyword args:
            new_system: target unit system passed to each
                :meth:`Parameter.to_units_system` call.
            include/exclude: optional key filters, as in :meth:`to_dict`.
        """
        new_system = filters.get('new_system')

        include = filters.get('include')
        exclude = filters.get('exclude')

        include_set = set(include) if include else None
        exclude_set = set(exclude) if exclude else None

        for key, value in self._children.items():
            if include_set is not None and key not in include_set:
                continue
            if exclude_set is not None and key in exclude_set:
                continue

            if isinstance(value, Node):
                value.to_units_system(**filters)
            elif isinstance(value, Parameter):
                self._children[key] = value.to_units_system(new_system)
            else:
                pass

    @property
    def parent(self):
        """Parent node, or None for a root node."""
        return self._parent() if self._parent else None
