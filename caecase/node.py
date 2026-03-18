#caecase/node.py
from .parameter import Parameter


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
        self._parent = parent
        self._children = {}

    def __getattr__(self, name):
        # print(self._children)
        if name.startswith('_'):
            raise AttributeError(f"!Атрибут '{name}' недоступен")
        if name == 'value':
            raise AttributeError(f"ВОТ ТУТ НАДО ВСТАВИТЬ ДОБАВЛЕНИЕ ПАРАМЕТРА")
        if name not in self._children:
            self._children[name] = Node(name=name, parent=self)  # Автосоздание узла
        return self._children[name]

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        if name == 'value':
            # super().__setattr__('value', 12)
            self._parent[self._name] = Parameter(value)
            del self
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

    def to_dict(self):
        """Преобразует узел в обычный словарь."""
        result = {}
        for key, value in self._children.items():
            if isinstance(value, Node):
                result[key] = value.to_dict()
            elif isinstance(value, Parameter):
                result[key] = value.to_dict()
                # result[key] = {
                #     "value": value.value,
                #     **{k: v for k, v in value.__dict__.items() if k != "value" and not k.startswith("_")}
                # }
            else:
                result[key] = value
        return result
