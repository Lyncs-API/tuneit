"Tunable variables"

__all__ = [
    "variable",
    "Variable",
]

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from .tunable import Tunable, Object, varname, compute


def variable(var, value=None, label=None, uid=None, fixed=False):
    """
    A tunable variable.

    Parameters
    ----------
    var: Iterable
        An iterator over the possible values of the variable
    value: Any
        The default value for the variable. If None the first element is used.
    label: str
        A label used to identify the variable
    uuid: Any
        Unique identifier for the variable.
    """
    label = label or varname()
    return Tunable(Variable(var, value=value, label=label, uid=uid, fixed=fixed))


@dataclass
class Variable(Object):
    "The Variable dataclass"
    _value: Any = None
    fixed: bool = False

    def __init__(self, var, value=None, fixed=False, **kwargs):
        if not isinstance(var, Iterable):
            raise TypeError("The first argument of Variable must be iterable")

        if value is None:
            self.value = next(iter(var))
        else:
            self.value = value
        self.fixed = fixed

        super().__init__(var, **kwargs)

    @property
    def value(self):
        "Value of the variable. If not fixed is a tunable object"
        if self.fixed:
            return self._value
        return Tunable(self)

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def var(self):
        "Alias of obj"
        return self.obj

    def __len__(self):
        return len(self.var)

    def __compute__(self):
        self.fixed = True
        return compute(self.value)

    @property
    def __dot_attrs__(self):
        return dict(shape="diamond", color="green" if self.fixed else "red")
